"""Load Person 1's handoff without modifying source values.

The loader normalizes column names into an internal representation. The original
CSV is copied verbatim into data/person2_scheduler_input.csv and is never rewritten.
"""
import csv
import math


def _as_float(value, name, row_number, errors):
    try:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError
        return number
    except (TypeError, ValueError):
        errors.append(f"row {row_number}: invalid numeric {name}")
        return 0.0


def load_and_validate(path, expected_rows=None, overload_threshold=80.0):
    with open(path, newline="", encoding="utf-8-sig") as f:
        source_rows = list(csv.DictReader(f))
    errors = []
    if not source_rows:
        return [], {"row_count": 0, "errors": ["CSV contains no data rows"], "valid": False,
                    "risk_score_source": None, "input_columns": []}

    columns = set(source_rows[0])
    person1_columns = {"timestamp_ms", "actual_cpu", "bilstm_predicted_cpu", "bilstm_predicted_overload"}
    legacy_columns = {"actual_cpu", "predicted_cpu", "p_overload", "actual_overload", "predicted_overload"}
    if person1_columns.issubset(columns):
        schema = "person1_bilstm_handoff"
        risk_source = "binary predicted_overload fallback (not a calibrated probability)"
    elif legacy_columns.issubset(columns):
        schema = "legacy_scheduler_handoff"
        risk_source = "p_overload column"
    else:
        missing_person1 = sorted(person1_columns - columns)
        missing_legacy = sorted(legacy_columns - columns)
        errors.append("unrecognized handoff schema; missing Person 1 columns: " + ", ".join(missing_person1)
                      + "; missing legacy columns: " + ", ".join(missing_legacy))
        return [], {"row_count": len(source_rows), "errors": errors, "valid": False,
                    "risk_score_source": None, "input_columns": sorted(columns)}

    if expected_rows is not None and len(source_rows) != expected_rows:
        errors.append(f"row count {len(source_rows)} != expected {expected_rows}")

    rows = []
    for i, raw in enumerate(source_rows, start=2):
        actual = _as_float(raw.get("actual_cpu"), "actual_cpu", i, errors)
        if schema == "person1_bilstm_handoff":
            predicted = _as_float(raw.get("bilstm_predicted_cpu"), "bilstm_predicted_cpu", i, errors)
            pred_label_value = _as_float(raw.get("bilstm_predicted_overload"), "bilstm_predicted_overload", i, errors)
            timestamp = _as_float(raw.get("timestamp_ms"), "timestamp_ms", i, errors)
            # No calibrated probability was supplied. Use the provided binary label
            # as a transparent 0/1 risk score, and report this limitation.
            p_overload = pred_label_value
        else:
            predicted = _as_float(raw.get("predicted_cpu"), "predicted_cpu", i, errors)
            p_overload = _as_float(raw.get("p_overload"), "p_overload", i, errors)
            pred_label_value = _as_float(raw.get("predicted_overload"), "predicted_overload", i, errors)
            timestamp = _as_float(raw.get("timestamp", i - 2), "timestamp", i, errors)

        pred_label = int(pred_label_value)
        if pred_label_value not in (0.0, 1.0):
            errors.append(f"row {i}: predicted_overload must be 0 or 1")
        if not 0.0 <= p_overload <= 1.0:
            errors.append(f"row {i}: p_overload/risk score outside [0,1]")

        # Actual labels are only for post-hoc evaluation; the scheduler objective
        # receives predicted_cpu and predicted_overload only.
        actual_label = int(actual >= overload_threshold)
        normalized = dict(raw)  # retain original values/columns in memory unchanged
        normalized.update({
            "timestamp": timestamp,
            "actual_cpu": actual,
            "predicted_cpu": predicted,
            "p_overload": p_overload,
            "actual_overload": actual_label,
            "predicted_overload": pred_label,
            "source_schema": schema,
        })
        rows.append(normalized)

    return rows, {"row_count": len(rows), "errors": errors, "valid": not errors,
                  "schema": schema, "risk_score_source": risk_source,
                  "input_columns": sorted(columns), "overload_threshold": overload_threshold,
                  "note": "timestamp_ms values in the supplied file look like Unix seconds; original column name/value preserved."}


def horizons(rows, length):
    if length < 1:
        raise ValueError("horizon length must be positive")
    return [rows[i:i + length] for i in range(0, len(rows), length)]
