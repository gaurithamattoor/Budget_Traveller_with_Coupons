import java.io.*;
import java.util.*;

public class Main {

    static class Flight {
        int from, to;
        long price;

        Flight(int from, int to, long price) {
            this.from = from;
            this.to = to;
            this.price = price;
        }
    }

    static class State {
        long cost;
        int city, flightCount, couponsUsed;
        State previous;
        Flight flight;
        boolean couponUsed;

        State(long cost, int city, int flightCount, int couponsUsed,
              State previous, Flight flight, boolean couponUsed) {
            this.cost = cost;
            this.city = city;
            this.flightCount = flightCount;
            this.couponsUsed = couponsUsed;
            this.previous = previous;
            this.flight = flight;
            this.couponUsed = couponUsed;
        }
    }

    static class Answer {
        long cost;
        List<Flight> path;
        List<Boolean> couponUsage;

        Answer(long cost, List<Flight> path, List<Boolean> couponUsage) {
            this.cost = cost;
            this.path = path;
            this.couponUsage = couponUsage;
        }
    }

    static int N, M, K, C;
    static final long INF = Long.MAX_VALUE / 4;
    static List<Flight> flights = new ArrayList<>();

    // Find the cheapest route using at most K stops and C coupons.
    static Answer findCheapestPath() {
        if (N == 1) {
            return new Answer(0, new ArrayList<>(), new ArrayList<>());
        }

        int maxFlights = K + 1;
        int maxCoupons = Math.min(C, maxFlights);

        long[][][] dp =
            new long[N + 1][maxFlights + 1][maxCoupons + 1];

        State[][][] states =
            new State[N + 1][maxFlights + 1][maxCoupons + 1];

        for (int city = 0; city <= N; city++) {
            for (int f = 0; f <= maxFlights; f++) {
                Arrays.fill(dp[city][f], INF);
            }
        }

        dp[1][0][0] = 0;
        states[1][0][0] =
            new State(0, 1, 0, 0, null, null, false);

        // Process routes with increasing numbers of flights.
        for (int usedFlights = 0; usedFlights < maxFlights; usedFlights++) {
            for (Flight flight : flights) {
                for (int usedCoupons = 0;
                     usedCoupons <= maxCoupons; usedCoupons++) {

                    long current =
                        dp[flight.from][usedFlights][usedCoupons];

                    if (current == INF) {
                        continue;
                    }

                    State previous =
                        states[flight.from][usedFlights][usedCoupons];

                    // Option 1: Pay the full price.
                    long normalCost = current + flight.price;

                    if (normalCost <
                        dp[flight.to][usedFlights + 1][usedCoupons]) {

                        dp[flight.to][usedFlights + 1][usedCoupons] =
                            normalCost;

                        states[flight.to][usedFlights + 1][usedCoupons] =
                            new State(
                                normalCost, flight.to, usedFlights + 1,
                                usedCoupons, previous, flight, false
                            );
                    }

                    // Option 2: Use one coupon on this flight.
                    if (usedCoupons < maxCoupons) {
                        long discountedCost =
                            current + flight.price / 2;

                        if (discountedCost <
                            dp[flight.to][usedFlights + 1][usedCoupons + 1]) {

                            dp[flight.to][usedFlights + 1]
                               [usedCoupons + 1] = discountedCost;

                            states[flight.to][usedFlights + 1]
                                  [usedCoupons + 1] =
                                new State(
                                    discountedCost, flight.to,
                                    usedFlights + 1, usedCoupons + 1,
                                    previous, flight, true
                                );
                        }
                    }
                }
            }
        }

        long bestCost = INF;
        State bestState = null;

        for (int f = 1; f <= maxFlights; f++) {
            for (int c = 0; c <= maxCoupons; c++) {
                if (dp[N][f][c] < bestCost) {
                    bestCost = dp[N][f][c];
                    bestState = states[N][f][c];
                }
            }
        }

        if (bestState == null) {
            return new Answer(-1, new ArrayList<>(), new ArrayList<>());
        }

        List<Flight> path = new ArrayList<>();
        List<Boolean> couponUsage = new ArrayList<>();

        State current = bestState;

        while (current != null && current.flight != null) {
            path.add(current.flight);
            couponUsage.add(current.couponUsed);
            current = current.previous;
        }

        Collections.reverse(path);
        Collections.reverse(couponUsage);

        return new Answer(bestCost, path, couponUsage);
    }

    // Option 1: Read graph from standard input.
    static void readFromInput(Scanner sc) {
        System.out.print("Enter N and M: ");
        N = sc.nextInt();
        M = sc.nextInt();

        System.out.print("Enter K (maximum stops) and C (coupons): ");
        K = sc.nextInt();
        C = sc.nextInt();

        flights.clear();

        System.out.println("Enter each flight as: from to price");

        for (int i = 0; i < M; i++) {
            flights.add(new Flight(
                sc.nextInt(), sc.nextInt(), sc.nextLong()
            ));
        }
    }

    // Option 2: Read graph from CSV.
    // CSV format: from,to,price
    static void readFromCSV(Scanner sc) throws IOException {
        System.out.print("Enter CSV filename: ");
        String filename = sc.next();

        System.out.print("Enter N (number of cities): ");
        N = sc.nextInt();

        System.out.print("Enter K and C: ");
        K = sc.nextInt();
        C = sc.nextInt();

        flights.clear();

        try (BufferedReader br =
                 new BufferedReader(new FileReader(filename))) {

            String line;

            while ((line = br.readLine()) != null) {
                line = line.trim();

                if (line.isEmpty()) {
                    continue;
                }

                String[] values = line.split(",");

                // Skip the header row.
                if (values[0].trim().equalsIgnoreCase("from")) {
                    continue;
                }

                if (values.length < 3) {
                    throw new IOException("Invalid CSV row: " + line);
                }

                flights.add(new Flight(
                    Integer.parseInt(values[0].trim()),
                    Integer.parseInt(values[1].trim()),
                    Long.parseLong(values[2].trim())
                ));
            }
        }

        M = flights.size();
    }

    // Option 3: Generate a random graph.
    // A chain 1 -> 2 -> ... -> N is included to guarantee
    // a route exists when K is large enough.
    static void generateGraph(Scanner sc) {
        System.out.print("Enter number of cities N: ");
        N = sc.nextInt();

        System.out.print("Enter K (maximum stops) and C (coupons): ");
        K = sc.nextInt();
        C = sc.nextInt();

        System.out.print("Enter number of additional random flights: ");
        int extra = sc.nextInt();

        if (N < 1 || K < 0 || C < 0 || extra < 0) {
            throw new IllegalArgumentException(
                "N must be positive; K, C and extra flights cannot be negative."
            );
        }

        flights.clear();
        Random random = new Random();

        // Add a guaranteed chain from city 1 to city N.
        for (int i = 1; i < N; i++) {
            flights.add(new Flight(
                i, i + 1, 100 + random.nextInt(901)
            ));
        }

        // Add random directed flights.
        for (int i = 0; i < extra && N > 1; i++) {
            int from = 1 + random.nextInt(N);
            int to = 1 + random.nextInt(N);

            if (from == to) {
                continue;
            }

            flights.add(new Flight(
                from, to, 100 + random.nextInt(1901)
            ));
        }

        M = flights.size();
    }

    // Save the generated graph before solving.
    static void writeGeneratedGraphCSV() throws IOException {
        try (PrintWriter pw =
                 new PrintWriter(new FileWriter("generated_flights.csv"))) {

            pw.println("from,to,price");

            for (Flight f : flights) {
                pw.printf(
                    Locale.US, "%d,%d,%d%n",
                    f.from, f.to, f.price
                );
            }
        }

        System.out.println(
            "Generated graph saved to: generated_flights.csv"
        );
    }

    // Save the graph and mark the selected route and coupon flights.
    static void writeResultCSV(Answer answer) throws IOException {
        Map<Flight, Boolean> selected = new IdentityHashMap<>();
        Map<Flight, Boolean> couponUsed = new IdentityHashMap<>();

        for (int i = 0; i < answer.path.size(); i++) {
            Flight f = answer.path.get(i);
            selected.put(f, true);
            couponUsed.put(f, answer.couponUsage.get(i));
        }

        try (PrintWriter pw = new PrintWriter(
                new FileWriter("budget_traveller_result.csv"))) {

            pw.println("from,to,price,on_selected_path,coupon_used");

            for (Flight f : flights) {
                pw.printf(
                    Locale.US, "%d,%d,%d,%s,%s%n",
                    f.from, f.to, f.price,
                    selected.containsKey(f) ? "x" : "",
                    Boolean.TRUE.equals(couponUsed.get(f)) ? "x" : ""
                );
            }
        }

        System.out.println(
            "Result graph saved to: budget_traveller_result.csv"
        );
    }

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);

        try {
            System.out.println("=== BUDGET TRAVELLER WITH COUPONS ===");
            System.out.println("1. Enter graph manually");
            System.out.println("2. Read graph from CSV");
            System.out.println("3. Generate random graph and save CSV");
            System.out.print("Choose option: ");

            int choice = sc.nextInt();

            switch (choice) {
                case 1:
                    readFromInput(sc);
                    break;

                case 2:
                    readFromCSV(sc);
                    break;

                case 3:
                    generateGraph(sc);
                    writeGeneratedGraphCSV();
                    break;

                default:
                    System.out.println("Invalid option.");
                    return;
            }

            if (N < 1 || K < 0 || C < 0) {
                System.out.println("Invalid N, K or C.");
                return;
            }

            for (Flight f : flights) {
                if (f.from < 1 || f.from > N ||
                    f.to < 1 || f.to > N || f.price < 0) {

                    System.out.println(
                        "Invalid flight: " + f.from + " -> " + f.to
                    );
                    return;
                }
            }

            Answer answer = findCheapestPath();

            System.out.println("\nMinimum cost: " + answer.cost);

            if (answer.cost != -1) {
                System.out.print("Path: 1");

                for (Flight f : answer.path) {
                    System.out.print(" -> " + f.to);
                }

                System.out.println("\nFlights used:");

                for (int i = 0; i < answer.path.size(); i++) {
                    Flight f = answer.path.get(i);
                    boolean coupon = answer.couponUsage.get(i);

                    long paid = coupon ? f.price / 2 : f.price;

                    System.out.printf(
                        Locale.US,
                        "%d -> %d | Original price: %d | Paid: %d | Coupon: %s%n",
                        f.from, f.to, f.price, paid,
                        coupon ? "Yes" : "No"
                    );
                }
            }

            writeResultCSV(answer);

        } catch (InputMismatchException e) {
            System.out.println(
                "Invalid input. Please enter values in the required format."
            );
        } catch (IOException e) {
            System.out.println("File error: " + e.getMessage());
        } catch (IllegalArgumentException e) {
            System.out.println("Input error: " + e.getMessage());
        } finally {
            sc.close();
        }
    }
}