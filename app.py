import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="AI Case Triage Prototype",
        layout="wide",
    )

    st.title("AI Case Triage Prototype")
    st.caption(
        "Local-first support case triage using Ollama + Llama, "
        "Pydantic validation, and Python routing."
    )

    st.subheader("Project status")
    st.info(
        "Project skeleton created successfully. "
        "Next we will add taxonomy, routing rules, and structured schemas."
    )

    st.subheader("Analyze case")
    case_text = st.text_area(
        "Paste a support case, email, or ticket description",
        height=180,
        placeholder="Example: I was charged twice for my subscription and need help today.",
    )

    customer_tier = st.selectbox(
        "Customer tier (optional)",
        ["", "Free", "Standard", "Premium", "Enterprise"],
    )

    product = st.text_input("Product (optional)")
    region = st.text_input("Region (optional)")
    current_queue = st.text_input("Current queue (optional)")

    if st.button("Analyze", type="primary"):
        if not case_text.strip():
            st.warning("Please enter a case description first.")
        else:
            st.success("UI skeleton is working. Analysis logic will be added next.")
            st.write(
                {
                    "case_text": case_text,
                    "customer_tier": customer_tier,
                    "product": product,
                    "region": region,
                    "current_queue": current_queue,
                }
            )

    st.divider()

    st.subheader("Re-triage")
    st.text_area(
        "Follow-up customer message",
        height=120,
        placeholder="Example: This issue is still blocking our team and we may cancel if it isn't fixed today.",
        disabled=True,
    )
    st.button("Re-evaluate", disabled=True)



if __name__ == "__main__":
    main()