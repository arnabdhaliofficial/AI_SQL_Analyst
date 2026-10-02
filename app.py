import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import sql

from agents.sql_analyst import sql_analyst


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI SQL Analyst",
    page_icon="🗄️",
    layout="wide"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    return psycopg2.connect(
        host=st.secrets["host"],
        port=st.secrets["port"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        dbname=st.secrets["database"]
    )


# ============================================================
# GET DATABASE SCHEMA
# ============================================================

def get_database_schema():

    connection = None
    cursor = None

    schema_data = []

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        # ----------------------------------------------------
        # Get all tables
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name;
            """
        )

        tables = cursor.fetchall()


        # ----------------------------------------------------
        # Process every table
        # ----------------------------------------------------

        for table_row in tables:

            table_name = table_row[0]

            # ------------------------------------------------
            # Get columns
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    column_name,
                    data_type,
                    is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                ORDER BY ordinal_position;
                """,
                (table_name,)
            )

            columns = cursor.fetchall()


            # ------------------------------------------------
            # Convert columns into DataFrame
            # ------------------------------------------------

            column_data = []

            for column in columns:

                column_data.append(
                    {
                        "Column Name": column[0],
                        "Data Type": column[1],
                        "Nullable": column[2]
                    }
                )


            columns_df = pd.DataFrame(
                column_data
            )


            # ------------------------------------------------
            # Get sample data
            # ------------------------------------------------

            sample_query = sql.SQL(
                "SELECT * FROM {}.{} LIMIT 5"
            ).format(
                sql.Identifier("public"),
                sql.Identifier(table_name)
            )

            cursor.execute(sample_query)

            sample_rows = cursor.fetchall()

            sample_columns = [
                description[0]
                for description in cursor.description
            ]

            sample_df = pd.DataFrame(
                sample_rows,
                columns=sample_columns
            )


            # ------------------------------------------------
            # Store table information
            # ------------------------------------------------

            schema_data.append(
                {
                    "table_name": table_name,
                    "columns": columns_df,
                    "sample_data": sample_df
                }
            )


        return schema_data, None


    except Exception as e:

        return [], str(e)


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# DISPLAY DATABASE SCHEMA
# ============================================================

def display_database_schema():

    st.header("🗄️ Database Schema")

    st.write(
        "Complete structure of the connected PostgreSQL database, "
        "including tables, columns, data types, and sample records."
    )


    with st.spinner("Loading database schema..."):

        schema_data, error = get_database_schema()


    # --------------------------------------------------------
    # Schema error
    # --------------------------------------------------------

    if error:

        st.error(
            f"Unable to load database schema: {error}"
        )

        return


    # --------------------------------------------------------
    # No tables
    # --------------------------------------------------------

    if not schema_data:

        st.warning(
            "No tables were found in the public schema."
        )

        return


    # --------------------------------------------------------
    # Number of tables
    # --------------------------------------------------------

    st.success(
        f"{len(schema_data)} table(s) found in the public schema."
    )


    # --------------------------------------------------------
    # Display every table
    # --------------------------------------------------------

    for table in schema_data:

        table_name = table["table_name"]

        columns_df = table["columns"]

        sample_df = table["sample_data"]


        with st.expander(
            f"📋 Table: {table_name}",
            expanded=False
        ):

            # ================================================
            # COLUMN INFORMATION
            # ================================================

            st.subheader("🧱 Columns")

            st.dataframe(
                columns_df,
                use_container_width=True,
                hide_index=True
            )


            # ================================================
            # SAMPLE DATA
            # ================================================

            st.subheader("👀 Sample Data")

            if not sample_df.empty:

                st.dataframe(
                    sample_df,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "This table currently contains no rows."
                )


# ============================================================
# APPLICATION HEADER
# ============================================================

st.title("🗄️ AI SQL Analyst")

st.write(
    "Ask questions about the database in natural language. "
    "The AI agent will curate your question, inspect the database "
    "schema, generate SQL, validate its safety, execute it, "
    "and display the database results."
)


# ============================================================
# DATABASE SCHEMA
# ============================================================

display_database_schema()


# ============================================================
# DIVIDER
# ============================================================

st.divider()


# ============================================================
# USER QUESTION
# ============================================================

st.header("💬 Ask a Database Question")

question = st.text_area(
    "Enter your question",
    placeholder=(
        "Example: "
        "What are the top 10 riders by number of completed rides?"
    ),
    height=100
)


# ============================================================
# RUN QUERY BUTTON
# ============================================================

if st.button(
    "Run Query",
    type="primary",
    use_container_width=True
):

    # --------------------------------------------------------
    # Validate question
    # --------------------------------------------------------

    if not question.strip():

        st.warning(
            "Please enter a question."
        )

        st.stop()


    # --------------------------------------------------------
    # Input state for LangGraph
    # --------------------------------------------------------

    input_schema = {

        "messages": [],

        "user_question": question,

        "curated_ques": "",

        "prompt_query_context": "",

        "generated_sql_query": "",

        "is_safe": "No",

        "comments": "",

        "sql_query_execution_result": {},

        "final_answer": ""
    }


    # ========================================================
    # RUN AI SQL AGENT
    # ========================================================

    with st.spinner(
        "🤖 AI SQL Agent is working..."
    ):

        try:

            response = sql_analyst.invoke(
                input_schema
            )

        except Exception as e:

            st.error(
                "❌ An error occurred while running the SQL agent."
            )

            st.exception(e)

            st.stop()


    # ========================================================
    # ANSWER
    # ========================================================

    st.divider()

    st.header("💬 Answer")


    # --------------------------------------------------------
    # Get safety status
    # --------------------------------------------------------

    safety_status = str(
        response.get(
            "is_safe",
            "No"
        )
    )


    # --------------------------------------------------------
    # Unsafe SQL
    # --------------------------------------------------------

    if safety_status.lower() != "yes":

        st.error(
            "The generated SQL query was not approved for execution."
        )

        judge_comments = response.get(
            "comments",
            ""
        )

        if judge_comments:

            st.write(
                f"**Reason:** {judge_comments}"
            )


    # --------------------------------------------------------
    # Safe SQL
    # --------------------------------------------------------

    else:

        st.success(
            "The query was executed successfully. "
            "The complete database results are shown below."
        )


    # ========================================================
    # GENERATED SQL
    # ========================================================

    st.divider()

    st.header("🔍 Generated SQL")

    generated_sql = response.get(
        "generated_sql_query",
        ""
    )


    if generated_sql:

        st.code(
            generated_sql,
            language="sql"
        )

    else:

        st.warning(
            "No SQL query was generated."
        )


    # ========================================================
    # SQL SAFETY CHECK
    # ========================================================

    st.header("🛡️ SQL Safety Check")

    col1, col2 = st.columns(
        [1, 3]
    )


    with col1:

        if safety_status.lower() == "yes":

            st.success(
                "SAFE"
            )

        else:

            st.error(
                "NOT SAFE"
            )


    with col2:

        judge_comments = response.get(
            "comments",
            ""
        )

        if judge_comments:

            st.write(
                judge_comments
            )


    # ========================================================
    # DATABASE RESULTS
    # ========================================================

    st.divider()

    st.header("📊 Database Results")


    execution_result = response.get(
        "sql_query_execution_result",
        {}
    )


    # --------------------------------------------------------
    # Make sure result is a dictionary
    # --------------------------------------------------------

    if isinstance(
        execution_result,
        dict
    ):

        # ====================================================
        # SQL EXECUTION ERROR
        # ====================================================

        if "error" in execution_result:

            st.error(
                execution_result["error"]
            )


        # ====================================================
        # SUCCESSFUL RESULT
        # ====================================================

        elif (
            "columns" in execution_result
            and "rows" in execution_result
        ):

            columns = execution_result["columns"]

            rows = execution_result["rows"]


            # ------------------------------------------------
            # Create DataFrame
            # ------------------------------------------------

            if rows:

                result_df = pd.DataFrame(
                    rows,
                    columns=columns
                )


                # ============================================
                # DISPLAY TABLE
                # ============================================

                st.dataframe(
                    result_df,
                    use_container_width=True,
                    hide_index=True
                )


                # ============================================
                # RESULT COUNT
                # ============================================

                st.caption(
                    f"{len(result_df)} row(s) returned."
                )


            else:

                st.info(
                    "The query executed successfully, "
                    "but returned no rows."
                )


        # ====================================================
        # UNKNOWN DICTIONARY FORMAT
        # ====================================================

        else:

            st.warning(
                "The database returned an unexpected result format."
            )

            st.json(
                execution_result
            )


    # --------------------------------------------------------
    # Unexpected result type
    # --------------------------------------------------------

    elif execution_result:

        st.write(
            execution_result
        )


    else:

        st.info(
            "No database results were returned."
        )


    # ========================================================
    # CURATED QUESTION
    # ========================================================

    st.divider()

    with st.expander(
        "📝 View Curated Question"
    ):

        curated_question = response.get(
            "curated_ques",
            ""
        )


        if curated_question:

            st.write(
                curated_question
            )

        else:

            st.info(
                "No curated question available."
            )