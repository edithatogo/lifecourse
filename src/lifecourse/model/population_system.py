import logging

import dask.dataframe as dd
import numpy as np
import pandas as pd
import psutil

from .cohort import gen_population_dask
from .dask_utils import ensure_known_divisions, safe_from_pandas
from .parameters import ABS_MORT, EMP_NP, LIFE_EXP_NP, START_YEAR
from .rng_utils import bernoulli, normal, poisson

logger = logging.getLogger(__name__)


def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


class PopulationSystemDask:
    def __init__(self, pop_size, current_params, arm="prospective"):
        self.arm = arm
        self.params = current_params
        # Generate a DataFrame with person_uids and merge into the public pop
        from .cohort import gen_person_uids

        base_pop_dd = gen_population_dask(pop_size, self.params, arm)
        # create a parallel dask dataframe for person_uids
        uids = gen_person_uids(pop_size)
        uids_df = safe_from_pandas(
            pd.DataFrame({"person_uid": uids}), npartitions=base_pop_dd.npartitions
        )
        # concatenate person_uid as the first column to keep backward compatibility
        # Ensure known divisions on the producers, then reset index on each
        # and re-ensure divisions before concatenation to avoid Dask warnings
        uids_df = ensure_known_divisions(uids_df)
        base_pop_dd = ensure_known_divisions(base_pop_dd)

        uids_df = uids_df.reset_index(drop=True)
        base_pop_dd = base_pop_dd.reset_index(drop=True)

        # After resetting indices, attempt to set explicit RangeIndex divisions.
        # Some Dask internals may refuse to mark `known_divisions` even after
        # calling ensure_known_divisions (depending on graph shape). As a
        # robust fallback, compute per-partition lengths for the authoritative
        # base population and rebuild both dataframes from delayed partitions
        # while assigning global RangeIndex offsets so divisions are explicit.
        try:
            # compute authoritative partition lengths from base population
            part_lens = base_pop_dd.map_partitions(len).compute()
            from dask import delayed

            part_lens = list(map(int, part_lens))
            offsets = [0]
            for ln in part_lens[:-1]:
                offsets.append(offsets[-1] + ln)
            last_idx = offsets[-1] + (part_lens[-1] if part_lens else 0) - 1
            divisions = tuple(offsets + [last_idx])

            # rebuild uids_df from the original uids array so partitions align
            # exactly with base_pop_dd. This guarantees the same divisions and
            # avoids relying on potentially noisy conversions.
            new_u_parts = []
            for i, ln in enumerate(part_lens):
                off = int(offsets[i]) if i < len(offsets) else 0
                start = offsets[i]
                end = start + ln
                slice_arr = np.array(uids[start:end], dtype=np.int64)

                @delayed
                def _uids_part(arr, off=off):
                    df = pd.DataFrame({"person_uid": arr})
                    df.index = pd.RangeIndex(off, off + len(df))
                    return df

                new_u_parts.append(_uids_part(slice_arr))

            uids_df = dd.from_delayed(
                new_u_parts,
                meta=pd.DataFrame({"person_uid": pd.Series(dtype=np.int64)}),
            )
            try:
                uids_df.divisions = divisions
            except (
                AttributeError,
                TypeError,
                ValueError,
            ) as exc:  # pragma: no cover - best-effort
                logger.debug("Could not set divisions on rebuilt uids_df: %s", exc)

            # rebuild base_pop_dd similarly to guarantee matched divisions
            b_parts = base_pop_dd.to_delayed()
            new_b_parts = []
            for i, part in enumerate(b_parts):
                off = int(offsets[i]) if i < len(offsets) else 0

                @delayed
                def _reindex_part_b(p, off=off):
                    if p is None:
                        return p
                    p.index = pd.RangeIndex(off, off + len(p))
                    return p

                new_b_parts.append(_reindex_part_b(part))

            base_pop_dd = dd.from_delayed(new_b_parts, meta=base_pop_dd._meta)
            try:
                base_pop_dd.divisions = divisions
            except (
                AttributeError,
                TypeError,
                ValueError,
            ) as exc:  # pragma: no cover - best-effort
                logger.debug("Could not set divisions on rebuilt base_pop_dd: %s", exc)
        except ValueError, TypeError:
            # Known, recoverable issues when computing partition lengths
            logger.exception("Recoverable error when computing partition lengths")
            uids_df = ensure_known_divisions(uids_df)
            base_pop_dd = ensure_known_divisions(base_pop_dd)
        except Exception:  # pragma: no cover - defensive
            # Unexpected errors: log with traceback but fall back safely.
            logger.exception("Unexpected error while aligning partitions")
            uids_df = ensure_known_divisions(uids_df)
            base_pop_dd = ensure_known_divisions(base_pop_dd)

        # Attach person_uid to each partition directly to avoid concat/division issues
        def _attach_uids(df_part):
            if df_part.empty:
                return df_part
            # df_part.index is a global RangeIndex after reindexing above
            idx = df_part.index.values.astype(int)
            try:
                df_part = df_part.copy()
                df_part["person_uid"] = uids[idx]
            except IndexError:
                # fallback: assign by position if indexing mismatch occurs
                logger.debug(
                    "IndexError when assigning person_uid by index; falling back to positional assignment"
                )
                df_part = df_part.copy()
                df_part["person_uid"] = np.arange(len(df_part))
            except Exception:  # pragma: no cover - defensive
                logger.exception("Unexpected error assigning person_uid")
                df_part = df_part.copy()
                df_part["person_uid"] = np.arange(len(df_part))
            return df_part

        meta_with_uid = base_pop_dd._meta.copy()
        meta_with_uid["person_uid"] = pd.Series(dtype=np.int64)
        self.pop = base_pop_dd.map_partitions(
            _attach_uids, meta=meta_with_uid
        ).persist()
        # Ensure explicit, known divisions for later concat/operations
        self.pop = ensure_known_divisions(self.pop)
        # Rechunk to optimize memory usage (now that divisions are known)
        self.pop = self.pop.repartition(npartitions=max(1, pop_size // 1000))

    def _mortality(self, year=None):
        # Backwards compatibility: if no year provided, use START_YEAR
        if year is None:
            year = START_YEAR
        params = self.params

        def mortality_partition(df):
            if df.empty:
                return df
            ages = df["age"].values
            sev = df["severity"].values
            age_indices = np.clip((ages // 5).astype(int), 0, len(ABS_MORT) - 1)
            surv_prob = ABS_MORT[age_indices] * params["MORT_HR"][sev]
            # stateless per-person survival draw: survive with prob = 1 - surv_prob
            uids = df.get("person_uid", np.arange(len(df)))
            p_survive = 1.0 - surv_prob
            survival = bernoulli(uids, p_survive, tag="mort", year=year)
            mask = (survival.astype(bool)) & (ages < LIFE_EXP_NP[sev])
            return df[mask]

        self.pop = self.pop.map_partitions(
            mortality_partition, meta=self.pop._meta
        ).persist()
        # Optimize partitions after operation
        self.pop = self.pop.repartition(npartitions=max(1, len(self.pop) // 1000))

    # Backwards-compatible signature: allow calling without year
    def _mortality_noarg(self):
        return self._mortality(START_YEAR)

    # Provide a _diagnosis method expected by older tests
    def _diagnosis(self, year=START_YEAR):
        # Run diagnosis logic on current population (delegates to fused code path per-year)
        # Implement minimal logic: apply diagnosis to familial, undiagnosed who meet min_test_age
        params = self.params

        def diag_partition(df):
            if df.empty:
                return df
            if self.arm != "prospective":
                return df
            mask = (
                (~df["diagnosed"])
                & df["familial"]
                & (df["age"] >= params["min_test_age"])
            )
            if mask.any():
                uids = df.loc[mask, "person_uid"].values
                df.loc[mask, "diagnosed"] = bernoulli(
                    uids, params["yield_wgs"], tag="diag", year=year
                )
            return df

        self.pop = self.pop.map_partitions(
            diag_partition, meta=self.pop._meta
        ).persist()
        self.pop = self.pop.repartition(npartitions=max(1, len(self.pop) // 1000))

    def _fertility(self):
        moms_dd = self.pop[(self.pop["sex"] == 0) & (self.pop["age"].between(15, 45))]

        # If there are no mothers (or partitions), return an empty DataFrame
        # with the expected population columns so callers can safely call
        # .compute() and iterate over the result.
        if moms_dd.npartitions == 0:
            empty = safe_from_pandas(
                pd.DataFrame(columns=self.pop._meta.columns), npartitions=1
            )
            return ensure_known_divisions(empty)

        moms_merged_dd = moms_dd.merge(
            self.params["FERT_RATES_DF"], on=["severity", "age"], how="left"
        )
        moms_merged_dd["rate"] = moms_merged_dd["rate"].fillna(0)

        def determine_births_and_familial_status(df_partition):
            if df_partition.empty:
                return pd.DataFrame(
                    {
                        "has_birth": pd.Series(dtype=bool),
                        "familial_parent": pd.Series(dtype=bool),
                        "parent_uid": pd.Series(dtype=np.int64),
                    },
                    index=df_partition.index,
                )
            rates = df_partition["rate"].values
            uids = df_partition.get("person_uid", np.arange(len(df_partition)))
            has_birth = bernoulli(uids, rates, tag="birth", year=START_YEAR).astype(
                bool
            )
            familial_parent = df_partition["familial"].values
            parent_uid = df_partition.get("person_uid", np.arange(len(df_partition)))
            return pd.DataFrame(
                {
                    "has_birth": has_birth,
                    "familial_parent": familial_parent,
                    "parent_uid": parent_uid,
                },
                index=df_partition.index,
            )

        birth_info_dd = moms_merged_dd.map_partitions(
            determine_births_and_familial_status,
            meta=pd.DataFrame(
                {
                    "has_birth": pd.Series(dtype=bool),
                    "familial_parent": pd.Series(dtype=bool),
                    "parent_uid": pd.Series(dtype=np.int64),
                },
                index=[],
            ),
        )

        actual_births_info_dd = birth_info_dd[birth_info_dd["has_birth"]]

        if actual_births_info_dd.npartitions == 0:
            empty = safe_from_pandas(
                pd.DataFrame(columns=self.pop._meta.columns), npartitions=1
            )
            return ensure_known_divisions(empty)

        def generate_babies_for_partition(
            partition_of_birth_info, params, arm, pop_meta
        ):
            n_babies_in_partition = len(partition_of_birth_info)
            if n_babies_in_partition == 0:
                return pop_meta.copy()
            # Generate deterministic child uids derived from parent_uid
            parent_uids = partition_of_birth_info["parent_uid"].values
            child_uids = []
            for i, pid in enumerate(parent_uids):
                # simple deterministic transformation, keep within 63 bits
                cid = (int(pid) * 1009 + (i + 1)) & ((1 << 63) - 1)
                child_uids.append(np.int64(cid))
            # Generate base baby rows with provided child_uids
            babies_df_part = gen_population_dask(
                n_babies_in_partition,
                params,
                arm,
                person_uids=np.array(child_uids, dtype=np.int64),
            ).compute()
            babies_df_part["age"] = 0
            babies_df_part["familial"] = partition_of_birth_info[
                "familial_parent"
            ].values
            babies_df_part["person_uid"] = np.array(child_uids, dtype=np.int64)
            # Ensure returned baby dataframe matches the authoritative population metadata
            try:
                return babies_df_part[pop_meta.columns]
            except KeyError:
                return babies_df_part.reindex(columns=pop_meta.columns)

        babies_dd = actual_births_info_dd.map_partitions(
            generate_babies_for_partition,
            self.params,
            self.arm,
            self.pop._meta,
            meta=self.pop._meta,
        )
        return babies_dd

    def _cost_qaly(self, year):
        """Compute costs and QALYs for the current population using stateless RNGs."""
        params = self.params

        def cost_qaly_partition(df):
            if df.empty:
                return df.assign(
                    cost_health=0.0,
                    cost_edu=0.0,
                    cost_respite=0.0,
                    cost_mobility=0.0,
                    cost_welfare=0.0,
                    cost_emp=0.0,
                    cost_morbidity=0.0,
                    annual_cost=0.0,
                    annual_qaly=0.0,
                    cost_ndis=0.0,
                    cost_carer=0.0,
                    cost_hospital=0.0,
                    cost_common_other=0.0,
                    income=0.0,
                )

            n = len(df)
            sev = df["severity"].values
            ages = df["age"].values
            disc = 1 / ((1 + params["DISCOUNT"]) ** (year - START_YEAR))

            hc = (
                params["COST_INP_NP"][sev]
                + params["COST_OUTP_NP"][sev]
                + params["COST_PHARM_NP"][sev]
            ) * disc
            rc = df["uses_respite"].values.astype(int) * params["RESPITE"] * disc
            mc = -df["needs_mobility"].values.astype(int) * params["MOBILITY"] * disc
            wc = params["WELFARE_NP"][sev] * disc
            emp = EMP_NP[df["employment"].values] * disc

            uids = df.get("person_uid", np.arange(n))
            lam = params["HOSP_RATE_NP"][sev]
            hosp_events = poisson(uids, lam, tag="hosp", year=year)
            cost_hospital = hosp_events * params["HOSP_COST"] * disc

            cost_common_other = (
                params["MENTAL_HEALTH_COST"] + params["INFORMAL_CARE_COST"]
            ) * disc

            ec = np.zeros(n, dtype=np.float64)
            m0 = df["school"] == 0
            m1 = df["school"] == 1
            if m0.any():
                ec[m0] = params["EDU"][0, df.loc[m0, "support"].values] * disc
            if m1.any():
                ec[m1] = params["EDU"][1, df.loc[m1, "support"].values] * disc

            morb_cost = np.zeros(n, dtype=np.float64)
            for i, k in enumerate(params["MORB_KEYS"]):
                p_arr = np.full(n, params["MORB_PROB"][k])
                m = bernoulli(uids, p_arr, tag=f"morb_{k}", year=year)
                morb_cost += m.astype(np.float64) * params["MORB_COST_NP"][i] * disc

            if self.arm == "prospective":
                m = df["diagnosed"].values
                morb_cost += (
                    m.astype(np.float64) * params["WGS_DIAG_COST_ADJUSTMENT"] * disc
                )

            morb_qaly = np.zeros(n, dtype=np.float64)
            for i, k in enumerate(params["MORB_KEYS"]):
                p_arr = np.full(n, params["MORB_PROB"][k])
                m = bernoulli(uids, p_arr, tag=f"morbq_{k}", year=year)
                morb_qaly += m.astype(np.float64) * params["MORB_QALY_NP"][i] * disc

            uq = params["U_BASE_NP"][sev] * np.exp(
                -params["U_DECAY"] * np.clip(ages - 20, 0, None)
            )
            diagnosed_mask = df["diagnosed"].values.astype(int)
            uq_with_diag = uq + diagnosed_mask * params["U_DIAG"]
            total_qaly = (uq_with_diag + params["U_CARER"]) * disc - morb_qaly

            if self.arm == "prospective":
                m = df["diagnosed"].values
                total_qaly += (
                    m.astype(np.float64) * params["WGS_DIAG_QALY_ADJUSTMENT"] * disc
                )

            df["annual_cost"] = hc + ec + rc + mc + wc + emp + morb_cost
            df["cost_health"] = hc
            df["cost_respite"] = rc
            df["annual_qaly"] = total_qaly
            df["cost_ndis"] = (
                df["diagnosed"].values.astype(int) * params["NDIS_COST"] * disc
            )
            df["cost_carer"] = params["CARER_HOURS_NP"][sev] * params["WAGE_HR"] * disc
            df["cost_mobility"] = mc
            df["cost_welfare"] = wc
            df["cost_emp"] = emp

            mu_sigma = []
            for idx in range(n):
                sev_i = df["severity"].iat[idx]
                edu = df["education"].iat[idx]
                sev_label = "mild" if sev_i == 0 else "severe"
                mu, sigma = params["INCOME_PARAMS"][sev_label][edu]
                mu_sigma.append((mu, sigma))
            df["income"] = np.exp(normal(uids, mu_sigma, tag="income", year=year))
            df["cost_hospital"] = cost_hospital
            df["cost_common_other"] = cost_common_other

            return df

        # apply over population
        self.pop = self.pop.map_partitions(
            cost_qaly_partition, meta=self.pop._meta
        ).persist()
        # Reset index to ensure unique, 0..N-1 integer index across the dataframe.
        # This avoids situations where .loc[row_index] returns multiple rows
        # (which produces a Series/DataFrame ambiguity in tests/assertions).
        try:
            self.pop = self.pop.reset_index(drop=True).persist()
            # Ensure known divisions so subsequent concatenations don't warn
            self.pop = ensure_known_divisions(self.pop)
        except Exception:
            # In case reset_index isn't appropriate for the current dask graph,
            # fall back to keeping existing pop but continue to repartition.
            logger.exception(
                "Unable to normalize partition divisions; retaining the current frame"
            )
        self.pop = self.pop.repartition(npartitions=max(1, len(self.pop) // 1000))

    def step_fused(self, year):
        """Prototype fused annual progression.

        This experimental method attempts to reduce intermediate materialization by
        performing mortality, diagnosis, age increment and cost/QALY calculations
        in a single map_partitions pass. Birth generation is performed from the
        pre-step population (to preserve fertility semantics), but no intermediate
        persist/repartition occurs between operations; a single persist is applied
        after concatenation. This is a low-risk prototype and keeps the original
        methods intact.
        """
        # Use stateless per-person randomness (rng_utils) instead of seeding global RNG

        orig_pop = self.pop

        # --- Generate babies from pre-step population (same logic as _fertility) ---
        moms_dd = orig_pop[(orig_pop["sex"] == 0) & (orig_pop["age"].between(15, 45))]

        if moms_dd.npartitions == 0:
            babies_dd = safe_from_pandas(
                pd.DataFrame(columns=self.pop.columns), npartitions=1
            )
            babies_dd = ensure_known_divisions(babies_dd)
        else:
            moms_merged_dd = moms_dd.merge(
                self.params["FERT_RATES_DF"], on=["severity", "age"], how="left"
            )
            moms_merged_dd["rate"] = moms_merged_dd["rate"].fillna(0)

            def determine_births_and_familial_status(df_partition):
                if df_partition.empty:
                    return pd.DataFrame(
                        {
                            "has_birth": pd.Series(dtype=bool),
                            "familial_parent": pd.Series(dtype=bool),
                        },
                        index=df_partition.index,
                    )
                rates = df_partition["rate"].values
                uids = df_partition.get("person_uid", np.arange(len(df_partition)))
                has_birth = bernoulli(uids, rates, tag="birth", year=year).astype(bool)
                familial_parent = df_partition["familial"].values
                parent_uid = df_partition.get(
                    "person_uid", np.arange(len(df_partition))
                )
                return pd.DataFrame(
                    {
                        "has_birth": has_birth,
                        "familial_parent": familial_parent,
                        "parent_uid": parent_uid,
                    },
                    index=df_partition.index,
                )

            birth_info_dd = moms_merged_dd.map_partitions(
                determine_births_and_familial_status,
                meta=pd.DataFrame(
                    {
                        "has_birth": pd.Series(dtype=bool),
                        "familial_parent": pd.Series(dtype=bool),
                        "parent_uid": pd.Series(dtype=np.int64),
                    },
                    index=[],
                ),
            )

            actual_births_info_dd = birth_info_dd[birth_info_dd["has_birth"]]

            if actual_births_info_dd.npartitions == 0:
                babies_dd = safe_from_pandas(
                    pd.DataFrame(columns=self.pop.columns), npartitions=1
                )
            else:

                def generate_babies_for_partition(
                    partition_of_birth_info, params, arm, pop_meta
                ):
                    n_babies_in_partition = len(partition_of_birth_info)
                    if n_babies_in_partition == 0:
                        return pop_meta.copy()
                    # Generate deterministic child uids derived from parent_uid
                    parent_uids = partition_of_birth_info["parent_uid"].values
                    child_uids = []
                    for i, pid in enumerate(parent_uids):
                        # simple deterministic transformation, keep within 63 bits
                        cid = (int(pid) * 1009 + (i + 1)) & ((1 << 63) - 1)
                        child_uids.append(np.int64(cid))
                    # Generate base baby rows with provided child_uids
                    babies_df_part = gen_population_dask(
                        n_babies_in_partition,
                        params,
                        arm,
                        person_uids=np.array(child_uids, dtype=np.int64),
                    ).compute()
                    babies_df_part["age"] = 0
                    babies_df_part["familial"] = partition_of_birth_info[
                        "familial_parent"
                    ].values
                    babies_df_part["person_uid"] = np.array(child_uids, dtype=np.int64)
                    # Ensure columns ordering matches the population meta
                    try:
                        return babies_df_part[pop_meta.columns]
                    except KeyError:
                        return babies_df_part.reindex(columns=pop_meta.columns)

                babies_dd = actual_births_info_dd.map_partitions(
                    generate_babies_for_partition,
                    self.params,
                    self.arm,
                    self.pop._meta,
                    meta=self.pop._meta,
                )
                babies_dd = ensure_known_divisions(babies_dd)

        # --- Fused per-partition update: mortality -> diagnosis -> age++ -> cost/qaly ---
        # Use self.params and self.arm directly within fused_partition to avoid
        # creating unused local variables that confuse linters.
        # expected column ordering (use meta to keep stable across partitions)
        expected_cols = list(self.pop._meta.columns)

        def fused_partition(df_partition, params, arm, year, expected_cols):
            if df_partition.empty:
                # return an empty DataFrame with expected columns
                return df_partition.reindex(columns=expected_cols)
            # mortality (based on current age)
            ages = df_partition["age"].values
            sev = df_partition["severity"].values
            age_indices = np.clip((ages // 5).astype(int), 0, len(ABS_MORT) - 1)
            surv_prob = ABS_MORT[age_indices] * params["MORT_HR"][sev]
            uids_all = df_partition.get("person_uid", np.arange(len(df_partition)))
            survive = bernoulli(uids_all, 1.0 - surv_prob, tag="mort", year=year)
            mask = (survive.astype(bool)) & (ages < LIFE_EXP_NP[sev])
            df = df_partition.loc[mask].copy()

            # diagnosis uses prior age (before increment) - stateless bernoulli
            if arm == "prospective" and not df.empty:
                diag_mask = (
                    (~df["diagnosed"])
                    & df["familial"]
                    & (df["age"] >= params["min_test_age"])
                )
                if diag_mask.any():
                    uids_diag = df.loc[diag_mask, "person_uid"].values
                    df.loc[diag_mask, "diagnosed"] = bernoulli(
                        uids_diag, params["yield_wgs"], tag="diag", year=year
                    )

            # increment age (match original ordering)
            df["age"] = df["age"] + 1

            # cost/qaly computation (stateless draws)
            n = len(df)
            if n == 0:
                return df.reindex(columns=expected_cols)

            sev = df["severity"].values
            ages2 = df["age"].values
            disc = 1 / ((1 + params["DISCOUNT"]) ** (year - START_YEAR))

            hc = (
                params["COST_INP_NP"][sev]
                + params["COST_OUTP_NP"][sev]
                + params["COST_PHARM_NP"][sev]
            ) * disc
            rc = df["uses_respite"].values.astype(int) * params["RESPITE"] * disc
            mc = -df["needs_mobility"].values.astype(int) * params["MOBILITY"] * disc
            wc = params["WELFARE_NP"][sev] * disc
            emp = EMP_NP[df["employment"].values] * disc

            import numpy as _np

            uids = df["person_uid"].values
            lam = params["HOSP_RATE_NP"][sev]
            hosp_events = poisson(uids, lam, tag="hosp", year=year)
            cost_hospital = hosp_events * params["HOSP_COST"] * disc

            cost_common_other = (
                params["MENTAL_HEALTH_COST"] + params["INFORMAL_CARE_COST"]
            ) * disc

            ec = _np.zeros(n, dtype=_np.float64)
            m0 = df["school"] == 0
            m1 = df["school"] == 1
            if m0.any():
                ec[m0] = params["EDU"][0, df.loc[m0, "support"].values] * disc
            if m1.any():
                ec[m1] = params["EDU"][1, df.loc[m1, "support"].values] * disc

            morb_cost = _np.zeros(n, dtype=_np.float64)
            for i, k in enumerate(params["MORB_KEYS"]):
                p_arr = _np.full(n, params["MORB_PROB"][k])
                m = bernoulli(uids, p_arr, tag=f"morb_{k}", year=year)
                morb_cost += m.astype(_np.float64) * params["MORB_COST_NP"][i] * disc

            if arm == "prospective":
                m = df["diagnosed"].values
                morb_cost += (
                    m.astype(_np.float64) * params["WGS_DIAG_COST_ADJUSTMENT"] * disc
                )

            morb_qaly = _np.zeros(n, dtype=_np.float64)
            for i, k in enumerate(params["MORB_KEYS"]):
                p_arr = _np.full(n, params["MORB_PROB"][k])
                m = bernoulli(uids, p_arr, tag=f"morbq_{k}", year=year)
                morb_qaly += m.astype(_np.float64) * params["MORB_QALY_NP"][i] * disc

            uq = params["U_BASE_NP"][sev] * _np.exp(
                -params["U_DECAY"] * _np.clip(ages2 - 20, 0, None)
            )
            diagnosed_mask = df["diagnosed"].values.astype(int)
            uq_with_diag = uq + diagnosed_mask * params["U_DIAG"]
            total_qaly = (uq_with_diag + params["U_CARER"]) * disc - morb_qaly

            if arm == "prospective":
                m = df["diagnosed"].values
                total_qaly += (
                    m.astype(_np.float64) * params["WGS_DIAG_QALY_ADJUSTMENT"] * disc
                )

            df["annual_cost"] = hc + ec + rc + mc + wc + emp + morb_cost
            df["cost_health"] = hc
            df["cost_respite"] = rc
            df["annual_qaly"] = total_qaly
            df["cost_ndis"] = (
                df["diagnosed"].values.astype(int) * params["NDIS_COST"] * disc
            )
            df["cost_carer"] = params["CARER_HOURS_NP"][sev] * params["WAGE_HR"] * disc
            df["cost_mobility"] = mc
            df["cost_welfare"] = wc
            df["cost_emp"] = emp
            # Income via stateless normal
            mu_sigma = []
            for idx in range(n):
                sev_i = df["severity"].iat[idx]
                edu = df["education"].iat[idx]
                sev_label = "mild" if sev_i == 0 else "severe"
                mu, sigma = params["INCOME_PARAMS"][sev_label][edu]
                mu_sigma.append((mu, sigma))
            df["income"] = np.exp(normal(uids, mu_sigma, tag="income", year=year))
            df["cost_hospital"] = cost_hospital
            df["cost_common_other"] = cost_common_other

            # Ensure column ordering matches expected metadata to avoid dask persist/compute errors
            try:
                return df[expected_cols]
            except KeyError:
                return df.reindex(columns=expected_cols)

        updated_pop = orig_pop.map_partitions(
            fused_partition,
            self.params,
            self.arm,
            year,
            expected_cols,
            meta=self.pop._meta,
        )

        # Concatenate babies (if any) and persist once
        if babies_dd.npartitions > 0:
            # Ensure both frames have known divisions before concatenation
            updated_pop = ensure_known_divisions(updated_pop)
            babies_dd = ensure_known_divisions(babies_dd)
            self.pop = dd.concat([updated_pop, babies_dd], interleave_partitions=True)
        else:
            self.pop = updated_pop

        self.pop = self.pop.persist()
        self.pop = self.pop.repartition(npartitions=max(1, len(self.pop) // 1000))

    def step(self, year):
        """Compatibility wrapper: call the fused prototype for now.

        This preserves the original public API while we continue converting
        the main `step` implementation to use stateless RNG helpers.
        """
        return self.step_fused(year)
