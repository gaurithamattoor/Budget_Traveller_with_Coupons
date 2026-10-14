import csv
import math
import os
import pygame

# ==========================================================
# BUDGET TRAVELLER WITH COUPONS
# Graph visualization + animated cheapest route
# Input: budget_traveller_result.csv from Main.java
# ==========================================================

pygame.init()

WIDTH, HEIGHT = 1250, 780
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Budget Traveller with Coupons")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
NAVY = (25, 58, 100)
DARK = (40, 47, 58)
GREY = (155, 166, 178)
LIGHT_GREY = (229, 234, 240)
PANEL = (244, 248, 253)
GREEN = (38, 174, 105)
RED = (231, 76, 76)
ORANGE = (255, 177, 58)
BLUE = (38, 112, 240)
GOLD = (255, 190, 0)
GOLD_DARK = (157, 108, 0)
BORDER = (210, 220, 233)

TITLE_FONT = pygame.font.SysFont("Arial", 29, bold=True)
HEADING_FONT = pygame.font.SysFont("Arial", 21, bold=True)
FONT = pygame.font.SysFont("Arial", 18)
SMALL_FONT = pygame.font.SysFont("Arial", 15)
NODE_FONT = pygame.font.SysFont("Arial", 20, bold=True)

# Layout: graph on the left, information panel on the right
GRAPH_RECT = pygame.Rect(20, 105, 835, 570)
PANEL_RECT = pygame.Rect(875, 105, 355, 570)

NODE_RADIUS = 23
STEP_DELAY = 1300


def load_flights(filename):
    """Read flights and selected-path information from CSV."""
    flights = []

    with open(filename, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("The CSV file is empty.")

        reader.fieldnames = [
            name.strip() for name in reader.fieldnames
        ]

        required = {"from", "to", "price"}
        if not required.issubset(reader.fieldnames):
            raise ValueError(
                "CSV needs columns: from,to,price"
            )

        for row in reader:
            source = int(row["from"])
            target = int(row["to"])
            price = int(float(row["price"]))

            if price < 0:
                raise ValueError("Flight prices cannot be negative.")

            selected = str(
                row.get("on_selected_path", "")
            ).strip().lower() == "x"

            coupon = str(
                row.get("coupon_used", "")
            ).strip().lower() == "x"

            flights.append({
                "from": source,
                "to": target,
                "price": price,
                "selected": selected,
                "coupon": coupon
            })

    return flights


def build_route(flights, start_city=1):
    """
    Follow selected edges in route order.
    Do not sort flights by city number.
    """
    selected = [
        flight for flight in flights if flight["selected"]
    ]

    route = []
    used = set()
    current = start_city

    while True:
        candidates = [
            (index, flight)
            for index, flight in enumerate(selected)
            if index not in used and flight["from"] == current
        ]

        if not candidates:
            break

        # Normally there should be one selected next edge.
        index, flight = candidates[0]
        route.append(flight)
        used.add(index)
        current = flight["to"]

    if len(route) != len(selected):
        raise ValueError(
            "Selected flights do not form one continuous route "
            "starting at city 1. Check the Java CSV output."
        )

    # A valid route should not repeat cities.
    cities = [start_city]
    for flight in route:
        cities.append(flight["to"])

    if len(cities) != len(set(cities)):
        raise ValueError(
            "The selected route contains a cycle. "
            "Check the Java algorithm's route reconstruction."
        )

    return route


def make_positions(cities):
    """Arrange nodes neatly inside the graph area."""
    cities = sorted(cities)
    count = len(cities)

    left = GRAPH_RECT.left + 70
    right = GRAPH_RECT.right - 70
    top = GRAPH_RECT.top + 85
    bottom = GRAPH_RECT.bottom - 75

    positions = {}

    if count == 1:
        positions[cities[0]] = (
            GRAPH_RECT.centerx, GRAPH_RECT.centery
        )
        return positions

    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    radius_x = max(80, (right - left) / 2)
    radius_y = max(70, (bottom - top) / 2)

    for index, city in enumerate(cities):
        angle = -math.pi / 2 + 2 * math.pi * index / count

        positions[city] = (
            int(center_x + radius_x * math.cos(angle)),
            int(center_y + radius_y * math.sin(angle))
        )

    return positions


def draw_text(text, x, y, color=DARK, font=FONT):
    surface = font.render(str(text), True, color)
    screen.blit(surface, (int(x), int(y)))


def draw_centered(text, x, y, color=DARK, font=FONT):
    surface = font.render(str(text), True, color)
    screen.blit(surface, surface.get_rect(center=(int(x), int(y))))


def draw_arrow(start, end, color, width=3):
    """Draw a directed flight arrow between two city nodes."""
    x1, y1 = start
    x2, y2 = end

    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)

    if length < 1:
        return

    ux, uy = dx / length, dy / length

    sx = x1 + ux * (NODE_RADIUS + 2)
    sy = y1 + uy * (NODE_RADIUS + 2)
    ex = x2 - ux * (NODE_RADIUS + 5)
    ey = y2 - uy * (NODE_RADIUS + 5)

    pygame.draw.line(
        screen, color, (sx, sy), (ex, ey), width
    )

    angle = math.atan2(ey - sy, ex - sx)
    arrow_length = 12
    spread = math.pi / 6

    left = (
        ex - arrow_length * math.cos(angle - spread),
        ey - arrow_length * math.sin(angle - spread)
    )
    right = (
        ex - arrow_length * math.cos(angle + spread),
        ey - arrow_length * math.sin(angle + spread)
    )

    pygame.draw.polygon(
        screen, color, [(ex, ey), left, right]
    )


def draw_edge_label(flight, start, end, color, offset=0):
    """Draw fare labels with a small perpendicular offset."""
    x1, y1 = start
    x2, y2 = end

    dx = x2 - x1
    dy = y2 - y1
    length = max(1, math.hypot(dx, dy))

    mx = (x1 + x2) / 2 - dy / length * (18 + offset)
    my = (y1 + y2) / 2 + dx / length * (18 + offset)

    if flight["coupon"]:
        label = f"{flight['price']} -> {flight['price'] // 2}"
        label_color = GOLD_DARK
    else:
        label = str(flight["price"])
        label_color = DARK

    surface = SMALL_FONT.render(label, True, label_color)
    rect = surface.get_rect(center=(int(mx), int(my)))
    background = rect.inflate(9, 6)

    pygame.draw.rect(
        screen, WHITE, background, border_radius=5
    )
    screen.blit(surface, rect)


def draw_graph(flights, route, positions, completed_count,
               current_city, start_city, destination):
    """Render all flights, then nodes on top of the edges."""
    screen.set_clip(GRAPH_RECT)

    # Group parallel flights so their labels can be separated.
    pair_counts = {}
    for flight in flights:
        key = (flight["from"], flight["to"])
        pair_counts[key] = pair_counts.get(key, 0) + 1

    pair_seen = {}

    for flight in flights:
        source = flight["from"]
        target = flight["to"]

        start = positions[source]
        end = positions[target]

        is_selected = flight["selected"]
        is_coupon = flight["coupon"]

        route_index = next(
            (
                i for i, item in enumerate(route)
                if item is flight
            ),
            -1
        )

        is_completed = (
            route_index >= 0 and route_index < completed_count
        )
        is_active = (
            route_index == completed_count
            and route_index >= 0
        )

        if is_coupon and (is_completed or is_active):
            color, width = GOLD, 5
        elif is_selected and (is_completed or is_active):
            color, width = BLUE, 5
        elif is_selected:
            color, width = (140, 180, 245), 3
        else:
            color, width = GREY, 2

        draw_arrow(start, end, color, width)

        key = (source, target)
        duplicate_index = pair_seen.get(key, 0)
        pair_seen[key] = duplicate_index + 1
        label_offset = duplicate_index * 14

        # Coupon prices are shown when their route flight is active
        # or has already been completed.
        if is_coupon and (is_active or is_completed):
            draw_edge_label(
                flight, start, end, color, label_offset
            )
        elif not is_coupon:
            draw_edge_label(
                flight, start, end, color, label_offset
            )

    for city, position in positions.items():
        if city == start_city:
            color = GREEN
        elif city == destination:
            color = RED
        elif city == current_city:
            color = GOLD
        elif any(
            route[i]["to"] == city
            for i in range(completed_count)
        ):
            color = ORANGE
        else:
            color = LIGHT_GREY

        pygame.draw.circle(
            screen, WHITE, position, NODE_RADIUS + 3
        )
        pygame.draw.circle(
            screen, color, position, NODE_RADIUS
        )
        pygame.draw.circle(
            screen, DARK, position, NODE_RADIUS, 2
        )

        draw_centered(
            city, position[0], position[1], DARK, NODE_FONT
        )

    screen.set_clip(None)


def draw_legend():
    """Draw a compact legend below the title."""
    items = [
        (GREEN, "Start"),
        (RED, "Destination"),
        (ORANGE, "Visited stop"),
        (BLUE, "Selected route"),
        (GOLD, "Coupon flight")
    ]

    x = 30
    y = 72

    for color, label in items:
        pygame.draw.circle(screen, color, (x + 8, y + 9), 7)
        draw_text(label, x + 21, y, DARK, SMALL_FONT)
        x += 150


def draw_status(route, completed_count, running_cost,
                coupons_used, current_city, start_city,
                destination, paused, finished, error_message):
    """Draw the information panel away from the graph."""
    pygame.draw.rect(
        screen, PANEL, PANEL_RECT, border_radius=15
    )
    pygame.draw.rect(
        screen, BORDER, PANEL_RECT, 2, border_radius=15
    )

    x = PANEL_RECT.x + 20
    y = PANEL_RECT.y + 20

    draw_text("JOURNEY STATUS", x, y, NAVY, HEADING_FONT)
    y += 48

    draw_text(f"Start city: {start_city}", x, y)
    y += 36

    draw_text(f"Current city: {current_city}", x, y)
    y += 36

    draw_text(f"Destination: {destination}", x, y)
    y += 36

    draw_text(
        f"Running cost: {running_cost}",
        x, y, GREEN, HEADING_FONT
    )
    y += 42

    draw_text(f"Flights used: {completed_count}", x, y)
    y += 36

    draw_text(f"Coupons used: {coupons_used}", x, y)
    y += 45

    pygame.draw.line(
        screen, BORDER, (x, y), (PANEL_RECT.right - 20, y), 2
    )
    y += 18

    draw_text("SELECTED ROUTE", x, y, NAVY, HEADING_FONT)
    y += 35

    route_cities = [start_city]
    for flight in route:
        route_cities.append(flight["to"])

    route_string = " -> ".join(map(str, route_cities))

    # Wrap route text if it is long.
    available_width = PANEL_RECT.width - 40
    words = route_string.split(" -> ")
    lines = []
    line = ""

    for word in words:
        candidate = word if not line else line + " -> " + word
        if SMALL_FONT.size(candidate)[0] <= available_width:
            line = candidate
        else:
            lines.append(line)
            line = word

    if line:
        lines.append(line)

    for route_line in lines[:3]:
        draw_text(route_line, x, y, DARK, SMALL_FONT)
        y += 23

    y += 14

    if error_message:
        draw_text("ROUTE ERROR", x, y, RED, HEADING_FONT)
        y += 30
        draw_text(error_message[:35], x, y, RED, SMALL_FONT)
    elif finished:
        draw_text(
            "JOURNEY COMPLETED!",
            x, y, GREEN, HEADING_FONT
        )
        y += 30
        draw_text("Press R to replay", x, y, DARK, SMALL_FONT)
    elif paused:
        draw_text("PAUSED", x, y, RED, HEADING_FONT)
    else:
        draw_text(
            "Journey in progress...",
            x, y, BLUE, SMALL_FONT
        )


def main():
    filename = "budget_traveller_result.csv"

    if not os.path.exists(filename):
        print(f"Cannot find {filename}.")
        print("Run Main.java first to create the CSV file.")
        return

    try:
        flights = load_flights(filename)

        if not flights:
            raise ValueError("The CSV contains no flights.")

        route = build_route(flights, start_city=1)

    except (OSError, ValueError, KeyError) as error:
        print("Error:", error)
        return

    all_cities = set()
    for flight in flights:
        all_cities.add(flight["from"])
        all_cities.add(flight["to"])

    start_city = 1

    if start_city not in all_cities:
        print("The graph does not contain start city 1.")
        return

    if route:
        destination = route[-1]["to"]
    else:
        # A CSV with no selected edges has no marked route.
        destination = max(all_cities)

    positions = make_positions(all_cities)

    completed_count = 0
    running_cost = 0
    coupons_used = 0
    current_city = start_city
    paused = False
    finished = False
    error_message = ""

    last_step_time = pygame.time.get_ticks()

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not finished:
                    paused = not paused
                    last_step_time = pygame.time.get_ticks()

                elif event.key == pygame.K_r:
                    completed_count = 0
                    running_cost = 0
                    coupons_used = 0
                    current_city = start_city
                    paused = False
                    finished = False
                    error_message = ""
                    last_step_time = pygame.time.get_ticks()

        now = pygame.time.get_ticks()

        if (
            not paused
            and not finished
            and not error_message
            and now - last_step_time >= STEP_DELAY
        ):
            if completed_count < len(route):
                flight = route[completed_count]

                # Verify that this flight continues from the
                # currently displayed city.
                if flight["from"] != current_city:
                    error_message = (
                        "Route order is invalid."
                    )
                else:
                    if flight["coupon"]:
                        running_cost += flight["price"] // 2
                        coupons_used += 1
                    else:
                        running_cost += flight["price"]

                    current_city = flight["to"]
                    completed_count += 1

                last_step_time = now
            else:
                finished = True

        screen.fill(WHITE)

        draw_text(
            "BUDGET TRAVELLER WITH COUPONS",
            25, 18, NAVY, TITLE_FONT
        )

        draw_text(
            "Space: Pause / Resume     R: Restart",
            28, 49, DARK, SMALL_FONT
        )

        draw_legend()

        # Graph boundary and title
        pygame.draw.rect(
            screen, WHITE, GRAPH_RECT, border_radius=12
        )
        pygame.draw.rect(
            screen, BORDER, GRAPH_RECT, 2, border_radius=12
        )

        draw_text(
            "FLIGHT NETWORK",
            GRAPH_RECT.x + 18,
            GRAPH_RECT.y + 15,
            NAVY,
            HEADING_FONT
        )

        draw_graph(
            flights,
            route,
            positions,
            completed_count,
            current_city,
            start_city,
            destination
        )

        draw_status(
            route,
            completed_count,
            running_cost,
            coupons_used,
            current_city,
            start_city,
            destination,
            paused,
            finished,
            error_message
        )

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()