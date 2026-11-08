import json
import streamlit as st

# ------------------------------------------------------------
# Scholarship Advisory System
# ------------------------------------------------------------

st.set_page_config(page_title="Scholarship Advisory System", page_icon="🎓")

# Default rules
DEFAULT_RULES = """[
  {
    "name": "Top merit candidate",
    "priority": 100,
    "conditions": [
      ["cgpa", ">=", 3.7],
      ["co_curricular_score", ">=", 80],
      ["family_income", "<=", 8000],
      ["disciplinary_actions", "==", 0]
    ],
    "action": {
      "decision": "AWARD_FULL",
      "reason": "Excellent academic & co-curricular performance, with acceptable need"
    }
  },
  {
    "name": "Good candidate - partial scholarship",
    "priority": 80,
    "conditions": [
      ["cgpa", ">=", 3.3],
      ["co_curricular_score", ">=", 60],
      ["family_income", "<=", 12000],
      ["disciplinary_actions", "<=", 1]
    ],
    "action": {
      "decision": "AWARD_PARTIAL",
      "reason": "Good academic & involvement record with moderate need"
    }
  },
  {
    "name": "Need-based review",
    "priority": 70,
    "conditions": [
      ["cgpa", ">=", 2.5],
      ["family_income", "<=", 4000]
    ],
    "action": {
      "decision": "REVIEW",
      "reason": "High need but borderline academic score"
    }
  },
  {
    "name": "Low CGPA – not eligible",
    "priority": 95,
    "conditions": [
      ["cgpa", "<", 2.5]
    ],
    "action": {
      "decision": "REJECT",
      "reason": "CGPA below minimum scholarship requirement"
    }
  },
  {
    "name": "Serious disciplinary record",
    "priority": 90,
    "conditions": [
      ["disciplinary_actions", ">=", 2]
    ],
    "action": {
      "decision": "REJECT",
      "reason": "Too many disciplinary records"
    }
  }
]"""

FIELDS = ["cgpa", "family_income", "co_curricular_score",
          "community_service_hours", "semester", "disciplinary_actions"]
OPERATORS = [">=", "<=", ">", "<", "==", "!="]
DECISIONS = ["AWARD_FULL", "AWARD_PARTIAL", "REVIEW", "REJECT"]


# ------------------------------------------------------------
# Rule engine
# ------------------------------------------------------------
def check_condition(facts, condition):
    """Check one condition like ["cgpa", ">=", 3.7] against the facts."""
    field, operator, value = condition
    fact_value = facts[field]

    if operator == ">=":
        return fact_value >= value
    elif operator == "<=":
        return fact_value <= value
    elif operator == ">":
        return fact_value > value
    elif operator == "<":
        return fact_value < value
    elif operator == "==":
        return fact_value == value
    elif operator == "!=":
        return fact_value != value
    else:
        raise ValueError("Unknown operator: " + str(operator))


def rule_matches(facts, rule):
    """A rule fires only if ALL of its conditions are true."""
    for condition in rule["conditions"]:
        if not check_condition(facts, condition):
            return False
    return True


def evaluate(facts, rules):
    """Return the winning rule (highest priority) and all fired rules."""
    sorted_rules = sorted(rules, key=lambda r: r["priority"], reverse=True)

    fired = []
    for rule in sorted_rules:
        if rule_matches(facts, rule):
            fired.append(rule)

    if len(fired) > 0:
        return fired[0], fired   
    return None, fired


# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------
if "rules" not in st.session_state:
    st.session_state.rules = json.loads(DEFAULT_RULES)
if "ver" not in st.session_state:
    st.session_state.ver = 0   


def refresh():
    """Bump the version so all editor widgets are rebuilt with fresh values."""
    st.session_state.ver += 1
    st.rerun()


def clean_number(x):
    """3.0 -> 3 so the JSON looks nicer."""
    if float(x) == int(x):
        return int(x)
    return float(x)


# ------------------------------------------------------------
# Page title + sidebar 
# ------------------------------------------------------------
st.title("🎓 Scholarship Advisory System")
st.write("A rule-based decision support tool for the scholarship committee.")

st.sidebar.header("Applicant Details")
cgpa = st.sidebar.number_input("CGPA", min_value=0.0, max_value=4.0, value=3.5, step=0.01)
family_income = st.sidebar.number_input("Monthly family income (RM)", min_value=0, value=5000, step=100)
co_curricular_score = st.sidebar.slider("Co-curricular score (0-100)", 0, 100, 70)
community_service_hours = st.sidebar.number_input("Community service hours", min_value=0, value=20, step=1)
semester = st.sidebar.number_input("Current semester", min_value=1, max_value=14, value=3, step=1)
disciplinary_actions = st.sidebar.number_input("Disciplinary actions", min_value=0, value=0, step=1)

facts = {
    "cgpa": cgpa,
    "family_income": family_income,
    "co_curricular_score": co_curricular_score,
    "community_service_hours": community_service_hours,
    "semester": semester,
    "disciplinary_actions": disciplinary_actions,
}

# ------------------------------------------------------------
# Rule editor
# ------------------------------------------------------------
st.subheader("Scholarship Rules")
st.caption("Rules with a higher priority number are checked first.")

tab1, tab2 = st.tabs(["📝 Easy Editor", "{ } JSON Editor"])

# ===== TAB 1: Easy editor 
with tab1:
    ver = st.session_state.ver
    rules = st.session_state.rules

    for i in range(len(rules)):
        rule = rules[i]
        title = rule["name"] + "  |  priority " + str(rule["priority"]) + "  →  " + rule["action"]["decision"]

        with st.expander(title):
            # basic info
            rule["name"] = st.text_input("Rule name", value=rule["name"], key=f"name_{ver}_{i}")
            col1, col2 = st.columns(2)
            rule["priority"] = col1.number_input("Priority", value=int(rule["priority"]),
                                                 step=1, key=f"pri_{ver}_{i}")

            # decision dropdown 
            options = DECISIONS.copy()
            if rule["action"]["decision"] not in options:
                options.append(rule["action"]["decision"])
            rule["action"]["decision"] = col2.selectbox(
                "Decision", options,
                index=options.index(rule["action"]["decision"]),
                key=f"dec_{ver}_{i}")

            rule["action"]["reason"] = st.text_input("Reason", value=rule["action"]["reason"],
                                                     key=f"reason_{ver}_{i}")

            # conditions
            st.markdown("**IF all of these are true:**")
            for j in range(len(rule["conditions"])):
                cond = rule["conditions"][j]
                c1, c2, c3, c4 = st.columns([3, 1.5, 2, 1])

                fields = FIELDS.copy()
                if cond[0] not in fields:
                    fields.append(cond[0])

                new_field = c1.selectbox("Field", fields, index=fields.index(cond[0]),
                                         key=f"f_{ver}_{i}_{j}", label_visibility="collapsed")
                new_op = c2.selectbox("Operator", OPERATORS,
                                      index=OPERATORS.index(cond[1]) if cond[1] in OPERATORS else 0,
                                      key=f"o_{ver}_{i}_{j}", label_visibility="collapsed")
                new_val = c3.number_input("Value", value=float(cond[2]), step=0.1, format="%g",
                                          key=f"v_{ver}_{i}_{j}", label_visibility="collapsed")
                rule["conditions"][j] = [new_field, new_op, clean_number(new_val)]

                if c4.button("🗑️", key=f"delc_{ver}_{i}_{j}", help="Delete this condition"):
                    rule["conditions"].pop(j)
                    refresh()

            b1, b2 = st.columns(2)
            if b1.button("➕ Add condition", key=f"addc_{ver}_{i}"):
                rule["conditions"].append(["cgpa", ">=", 0])
                refresh()
            if b2.button("❌ Delete this rule", key=f"delr_{ver}_{i}"):
                rules.pop(i)
                refresh()

    # add rule / reset buttons
    a1, a2 = st.columns(2)
    if a1.button("➕ Add new rule"):
        rules.append({
            "name": "New rule",
            "priority": 50,
            "conditions": [["cgpa", ">=", 0]],
            "action": {"decision": "REVIEW", "reason": "Write the reason here"}
        })
        refresh()
    if a2.button("🔄 Reset to default rules"):
        st.session_state.rules = json.loads(DEFAULT_RULES)
        refresh()

# ===== TAB 2: JSON editor =====
with tab2:
    st.caption("Advanced: edit the raw JSON, then click 'Apply JSON'.")
    current_json = json.dumps(st.session_state.rules, indent=2, ensure_ascii=False)
    
    json_text = st.text_area("Rules (JSON)", value=current_json, height=400,
                             key="json_" + str(hash(current_json)))

    if st.button("✅ Apply JSON"):
        try:
            new_rules = json.loads(json_text)
            st.session_state.rules = new_rules
            refresh()
        except json.JSONDecodeError as e:
            st.error("Invalid JSON: " + str(e))

# ------------------------------------------------------------
# Evaluate applicant
# ------------------------------------------------------------
st.divider()

if st.button("Evaluate Applicant", type="primary"):
    try:
        winner, fired = evaluate(facts, st.session_state.rules)
    except KeyError as e:
        st.error("Unknown field used in a rule: " + str(e))
        st.stop()
    except Exception as e:
        st.error("Error in rules: " + str(e))
        st.stop()

    st.subheader("Result")
    if winner is None:
        st.warning("No rule matched. Please review this applicant manually.")
    else:
        decision = winner["action"]["decision"]

        if decision in ("AWARD_FULL", "AWARD_PARTIAL"):
            st.success("Decision: " + decision)
        elif decision == "REVIEW":
            st.warning("Decision: " + decision)
        else:
            st.error("Decision: " + decision)

        st.write("**Rule applied:** " + winner["name"] + " (priority " + str(winner["priority"]) + ")")
        st.write("**Reason:** " + winner["action"]["reason"])

        st.subheader("All rules that matched")
        table = []
        for r in fired:
            table.append({
                "Rule": r["name"],
                "Priority": r["priority"],
                "Decision": r["action"]["decision"],
            })
        st.table(table)

    with st.expander("Applicant facts used"):
        st.json(facts)