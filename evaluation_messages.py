import json
import os
import csv
from collections import defaultdict

DISTRESS_MAP = {
    "none": 0,
    "mild": 1,
    "moderate": 2,
    "high": 3,
    "crisis": 4
}

def load_logs(path="conversation_logs.json"):
    if not os.path.exists(path):
        print("No logs file found.")
        return []

    with open(path, "r") as f:
        data = json.load(f)

    # If the top-level is a list containing a list, flatten it
    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], list):
        return data[0]

    return data

def group_by_session(logs):
    sessions = defaultdict(list)
    for entry in logs:
        sid = entry.get("session_id")
        if sid:
            sessions[sid].append(entry)
    return sessions

def export_message_level_csv(log_path="conversation_logs.json",
                             out_path="message_level_support_styles.csv"):
    logs = load_logs(log_path)
    sessions = group_by_session(logs)

    fields = [
        "session_id",
        "message_index",
        "user_message",
        "message_type",
        "classifier_style",
        "support_style",
        "distress_level_label",
        "distress_level_num",
        "prev_distress_level_num",
        "distress_delta",
        "risk",
        "tone",
        "emotional_indicators",
        "other_notes"
    ]

    rows = []

    for sid, entries in sessions.items():
        entries = list(entries)

        prev_distress = None
        msg_idx = 0

        for e in entries:
            if "user_message" not in e:
                continue

            msg_idx += 1

            inferred = e.get("inferred_state", {})
            distress_label = inferred.get("distress_level", "none")
            distress_num = DISTRESS_MAP.get(distress_label, 0)

            if prev_distress is None:
                delta = None
            else:
                delta = distress_num - prev_distress

            row = {
                "session_id": sid,
                "message_index": msg_idx,
                "user_message": e.get("user_message"),
                "message_type": e.get("message_type"),
                "classifier_style": e.get("classifier_style"),
                "support_style": e.get("support_style"),
                "distress_level_label": distress_label,
                "distress_level_num": distress_num,
                "prev_distress_level_num": prev_distress,
                "distress_delta": delta,
                "risk": e.get("risk", 0),
                "tone": e.get("tone"),
                "emotional_indicators": inferred.get("emotional_indicators", []),
                "other_notes": inferred.get("other_notes", "")
            }

            rows.append(row)
            prev_distress = distress_num

    if not rows:
        print("No message rows to export.")
        return

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported message-level CSV to {out_path}")

if __name__ == "__main__":
    export_message_level_csv()