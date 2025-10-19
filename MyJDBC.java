import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class MyJDBC {
    public static void main(String[] args) {
        String url = "jdbc:mysql://127.0.0.1:3306/anirudh?serverTimezone=UTC";
        String user = "root";
        String password = "disco";
        String csvFile = "C:\\Users\\aniru\\PycharmProjects\\YTAnalyzer\\comments.csv";

        try (Connection connection = DriverManager.getConnection(url, user, password)) {
            if (connection != null && !connection.isClosed()) {
                System.out.println("SUCCESS: Database connected successfully!");
            }

            // --- Create table if not exists ---
            String createTableQuery = "CREATE TABLE IF NOT EXISTS USER (" +
                    "s_no INT PRIMARY KEY, " +
                    "comments TEXT, " +
                    "sentiment_analysis VARCHAR(50))";
            try (Statement createStmt = connection.createStatement()) {
                createStmt.execute(createTableQuery);
            }
            System.out.println("SUCCESS: USER table is ready.");

            // --- Use REPLACE INTO to update if exists ---
            String insertOrReplaceQuery = "REPLACE INTO USER (s_no, comments, sentiment_analysis) VALUES (?, ?, ?)";
            PreparedStatement preparedStatement = connection.prepareStatement(insertOrReplaceQuery);

            // --- Read CSV ---
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

                    // Skip header row
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

            // --- Fetch all data ---
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

    // --- Simple CSV parser (handles quotes & commas) ---
    private static List<String> parseCSVLine(String line) {
        List<String> tokens = new ArrayList<>();
        StringBuilder sb = new StringBuilder();
        boolean inQuotes = false;

        for (char c : line.toCharArray()) {
            if (c == '"') {
                inQuotes = !inQuotes; // Stoggle quote mode
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
