import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

/**
 * ------------------------------------------------------------------------------------------
 * Project: YTAnalyzer - Java JDBC Integration Module
 * ------------------------------------------------------------------------------------------
 * Purpose:
 * This Java program reads YouTube comment data from a CSV file and inserts it into a MySQL
 * database table using JDBC (Java Database Connectivity). It also retrieves and displays the
 * inserted data back to the console for verification.
 *
 * Author: [Your Name]
 * Date: October 2025
 * ------------------------------------------------------------------------------------------
 * Key Features:
 * 1. Connects to a MySQL database using JDBC.
 * 2. Automatically creates a table "USER" if it doesn’t exist.
 * 3. Reads data from a local CSV file (with comment text and sentiment).
 * 4. Inserts or updates data into the database using "REPLACE INTO".
 * 5. Fetches and prints all entries to the console.
 * 6. Includes error handling for invalid data and SQL/IO exceptions.
 *
 * ------------------------------------------------------------------------------------------
 * Step-by-Step Explanation:
 * ------------------------------------------------------------------------------------------
 * 1️⃣  Establishing a JDBC Connection:
 *      - The MySQL database connection is made using:
 *          DriverManager.getConnection(url, user, password)
 *      - The URL includes "serverTimezone=UTC" to ensure consistent time zone handling.
 *
 * 2️⃣  Creating a Table (if it doesn’t exist):
 *      - The code executes a CREATE TABLE IF NOT EXISTS statement for table "USER".
 *      - Columns:
 *          s_no (INT, PRIMARY KEY)
 *          comments (TEXT)
 *          sentiment_analysis (VARCHAR)
 *
 * 3️⃣  Reading from CSV File:
 *      - The program uses BufferedReader to read each line.
 *      - A helper method parseCSVLine() safely splits the CSV data while handling commas inside quotes.
 *
 * 4️⃣  Skipping Header Row:
 *      - The first row (if starts with "s_no") is skipped automatically.
 *
 * 5️⃣  Using PreparedStatement:
 *      - Query: REPLACE INTO USER (s_no, comments, sentiment_analysis)
 *      - This replaces rows if the same s_no already exists.
 *
 * 6️⃣  Handling Errors:
 *      - Catches IOException for file reading issues.
 *      - Catches SQLException for database errors.
 *      - Catches NumberFormatException for bad numeric data.
 *
 * 7️⃣  Displaying Inserted Data:
 *      - After insertion, SELECT * FROM USER fetches all rows.
 *      - Results are printed line by line.
 *
 * ------------------------------------------------------------------------------------------
 * Notes:
 * ------------------------------------------------------------------------------------------
 * - Ensure MySQL is running and the 'anirudh' database exists.
 * - Update 'csvFile' path to your correct local file location.
 * - Make sure the JDBC driver (Connector/J) is added to your Java classpath.
 *
 * ------------------------------------------------------------------------------------------
 * Educational Purpose:
 * ------------------------------------------------------------------------------------------
 * This code demonstrates:
 * - End-to-end data flow between Python and Java (via CSV)
 * - Basic CRUD operations using JDBC
 * - Integration between machine learning (Python/TextBlob) and database storage (Java/MySQL)
 *
 * ------------------------------------------------------------------------------------------
 */

public class MyJDBC {
    public static void main(String[] args) {
        String url = "jdbc:mysql:";
        String user = "root";
        String password = "";
        String csvFile = "";

        try (Connection connection = DriverManager.getConnection(url, user, password)) {
            if (connection != null && !connection.isClosed()) {
                System.out.println("SUCCESS: Database connected successfully!");
            }

            // --- Step 1: Create table if it does not exist ---
            String createTableQuery = "CREATE TABLE IF NOT EXISTS USER (" +
                    "s_no INT PRIMARY KEY, " +
                    "comments TEXT, " +
                    "sentiment_analysis VARCHAR(50))";
            try (Statement createStmt = connection.createStatement()) {
                createStmt.execute(createTableQuery);
            }
            System.out.println("SUCCESS: USER table is ready.");

            // --- Step 2: Insert or update data using REPLACE INTO ---
            String insertOrReplaceQuery = "REPLACE INTO USER (s_no, comments, sentiment_analysis) VALUES (?, ?, ?)";
            PreparedStatement preparedStatement = connection.prepareStatement(insertOrReplaceQuery);

            // --- Step 3: Read and parse CSV file ---
            try (BufferedReader br = new BufferedReader(new FileReader(csvFile))) {
                String line;
                int rowCount = 0;
                int inserted = 0;

                while ((line = br.readLine()) != null) {
                    line = line.replace("\uFEFF", "").trim();
                    if (line.isEmpty()) continue;

                    List<String> tokens = parseCSVLine(line);
                    if (tokens.size() < 3) {
                        System.out.println("WARNING: Skipping invalid row: " + line);
                        continue;
                    }

                    // --- Skip header row ---
                    if (rowCount == 0 && tokens.get(0).equalsIgnoreCase("s_no")) {
                        rowCount++;
                        continue;
                    }

                    try {
                        int s_no = Integer.parseInt(tokens.get(0).trim());
                        String comments = tokens.get(1).trim();
                        String sentiment = tokens.get(2).trim();

                        preparedStatement.setInt(1, s_no);
                        preparedStatement.setString(2, comments);
                        preparedStatement.setString(3, sentiment);
                        preparedStatement.executeUpdate();
                        inserted++;
                    } catch (NumberFormatException e) {
                        System.out.println("WARNING: Skipping invalid number row: " + line);
                    }

                    rowCount++;
                }
                System.out.println("SUCCESS: CSV import complete. Rows inserted/replaced: " + inserted);
            } catch (IOException e) {
                System.out.println("ERROR: Error reading CSV: " + e.getMessage());
            }

            // --- Step 4: Fetch and display all data ---
            try (Statement statement = connection.createStatement();
                 ResultSet resultSet = statement.executeQuery("SELECT * FROM USER")) {

                boolean found = false;
                while (resultSet.next()) {
                    int s_no = resultSet.getInt("s_no");
                    String comments = resultSet.getString("comments");
                    String sentiment = resultSet.getString("sentiment_analysis");
                    System.out.println("S.No: " + s_no + " | Sentiment: " + sentiment + " | Comment: " + comments);
                    found = true;
                }

                if (!found) {
                    System.out.println("WARNING: No data found in USER table!");
                }
            }

        } catch (SQLException e) {
            System.out.println("ERROR: Database error: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * --------------------------------------------------------------------------------------
     * Helper Method: parseCSVLine
     * --------------------------------------------------------------------------------------
     * Description:
     *  This method safely parses a single line of CSV text into a list of strings,
     *  handling quoted fields that contain commas (e.g., "hello, world").
     *
     * Logic:
     *  - Iterate through each character in the line.
     *  - Toggle inQuotes when encountering a quote mark.
     *  - Split only on commas that are outside quotes.
     *
     * Input:
     *  - line (String): A single CSV record.
     *
     * Output:
     *  - List<String>: Parsed tokens for each column.
     * --------------------------------------------------------------------------------------
     */
    private static List<String> parseCSVLine(String line) {
        List<String> tokens = new ArrayList<>();
        StringBuilder sb = new StringBuilder();
        boolean inQuotes = false;

        for (char c : line.toCharArray()) {
            if (c == '"') {
                inQuotes = !inQuotes;
            } else if (c == ',' && !inQuotes) {
                tokens.add(sb.toString());
                sb.setLength(0);
            } else {
                sb.append(c);
            }
        }
        tokens.add(sb.toString());
        return tokens;
    }
}

/*
-----------------------------------------------------------------------------------------------
Additional Notes:
-----------------------------------------------------------------------------------------------
This program is a core part of the YTAnalyzer project, bridging machine learning (Python)
and database storage (Java + MySQL). The CSV is created by the Python module after
sentiment analysis using TextBlob or Gemini LLM. The Java code then stores this data
into a structured SQL table, enabling easy retrieval, analytics, and visualization.

The approach used here demonstrates:
- Cross-language interoperability between Python and Java.
- Secure, structured data handling using JDBC.
- Automated database schema creation and population.
-----------------------------------------------------------------------------------------------
*/
