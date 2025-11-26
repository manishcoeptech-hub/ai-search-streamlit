import streamlit as st
import time
import heapq

# ---------- 8-puzzle core logic ----------

MOVES = {
    0: [1, 3],
    1: [0, 2, 4],
    2: [1, 5],
    3: [0, 4, 6],
    4: [1, 3, 5, 7],
    5: [2, 4, 8],
    6: [3, 7],
    7: [4, 6, 8],
    8: [5, 7],
}


def parse_state(text: str):
    """Parse '1 8 7 0 3 5 2 4 6' -> [1,8,7,0,3,5,2,4,6] with basic validation."""
    parts = text.replace(",", " ").split()
    if len(parts) != 9:
        raise ValueError("You must enter exactly 9 numbers.")
    nums = [int(x) for x in parts]
    if sorted(nums) != list(range(9)):
        raise ValueError("State must contain all numbers from 0 to 8 exactly once.")
    return nums


def count_inversions(state):
    arr = [x for x in state if x != 0]
    inv = 0
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] > arr[j]:
                inv += 1
    return inv


def is_solvable(state):
    # For standard 8 puzzle with goal [1..8,0]: solvable iff inversions even.
    return count_inversions(state) % 2 == 0


def h_misplaced(state, goal):
    return sum(1 for i in range(9) if state[i] != goal[i] and state[i] != 0)


def reconstruct_path(came_from, current):
    path = [current]
    while tuple(current) in came_from:
        current = came_from[tuple(current)]
        if current is None:
            break
        path.append(current)
    path.reverse()
    return path


def a_star_misplaced(start, goal):
    """A* search with misplaced-tile heuristic."""
    start_t = tuple(start)
    goal_t = tuple(goal)

    open_list = []
    heapq.heappush(open_list, (0, start_t))
    came_from = {start_t: None}
    g_score = {start_t: 0}

    expanded = 0

    while open_list:
        _, current = heapq.heappop(open_list)
        expanded += 1

        if current == goal_t:
            return reconstruct_path(came_from, list(current)), expanded

        blank = current.index(0)
        for m in MOVES[blank]:
            neighbor = list(current)
            neighbor[blank], neighbor[m] = neighbor[m], neighbor[blank]
            n_t = tuple(neighbor)

            tentative_g = g_score[current] + 1
            if n_t not in g_score or tentative_g < g_score[n_t]:
                g_score[n_t] = tentative_g
                f = tentative_g + h_misplaced(neighbor, goal)
                heapq.heappush(open_list, (f, n_t))
                came_from[n_t] = list(current)

    return None, expanded


from collections import deque


def bfs(start, goal):
    """Uninformed Breadth-First Search."""
    start_t = tuple(start)
    goal_t = tuple(goal)

    queue = deque([start_t])
    came_from = {start_t: None}
    expanded = 0

    while queue:
        current = queue.popleft()
        expanded += 1

        if current == goal_t:
            return reconstruct_path(came_from, list(current)), expanded

        blank = current.index(0)
        for m in MOVES[blank]:
            neighbor = list(current)
            neighbor[blank], neighbor[m] = neighbor[m], neighbor[blank]
            n_t = tuple(neighbor)
            if n_t not in came_from:
                came_from[n_t] = list(current)
                queue.append(n_t)

    return None, expanded


# ---------- UI helpers ----------

def render_state_html(state):
    """Return HTML for a 3x3 puzzle grid."""
    html = """
    <style>
    .grid { display: inline-grid; grid-template-columns: repeat(3, 60px); gap: 6px; }
    .tile {
        width: 60px; height: 60px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 10px;
        font-size: 28px; font-weight: 600;
        background: #e0e0e0;
        border: 2px solid #555;
    }
    .blank {
        background: #999;
        border: 2px solid #555;
    }
    </style>
    <div class="grid">
    """
    for v in state:
        if v == 0:
            html += '<div class="tile blank"></div>'
        else:
            html += f'<div class="tile">{v}</div>'
    html += "</div>"
    return html


# ---------- Streamlit app ----------

st.set_page_config(page_title="8-Puzzle Search Lab", page_icon="🧩", layout="centered")

st.title("🧩 8-Puzzle Search Lab (Streamlit)")
st.markdown(
    """
Use this interactive lab to **visualize search algorithms** on the 8-puzzle.

1. Enter a **start state** and **goal state**  
2. Choose an **algorithm**  
3. Watch the puzzle being solved **step by step**
"""
)

col1, col2 = st.columns(2)

with col1:
    start_text = st.text_input(
        "Start state (9 numbers, 0 = blank)",
        "1 8 7 0 3 5 2 4 6",
    )

with col2:
    goal_text = st.text_input(
        "Goal state (9 numbers, 0 = blank)",
        "1 2 3 4 5 6 7 8 0",
    )

algo = st.selectbox(
    "Algorithm",
    ["A* (Misplaced Tile)", "Breadth-First Search (BFS)"],
)

speed = st.slider("Animation speed (seconds per step)", 0.1, 1.0, 0.5, 0.1)

solve_btn = st.button("🔍 Solve")

st.markdown("---")

if solve_btn:
    # Parse & validate
    try:
        start_state = parse_state(start_text)
        goal_state = parse_state(goal_text)
    except Exception as e:
        st.error(f"Input error: {e}")
        st.stop()

    # Check solvable
    if not is_solvable(start_state):
        st.error(
            f"The chosen start state has **{count_inversions(start_state)} inversions** "
            "and is **not solvable** for this goal configuration."
        )
        st.stop()

    st.success("Puzzle is solvable. Running search...")

    # Run selected algorithm
    t0 = time.time()
    if algo.startswith("A*"):
        path, expanded = a_star_misplaced(start_state, goal_state)
    else:
        path, expanded = bfs(start_state, goal_state)
    t1 = time.time()

    if path is None:
        st.error("No solution found (this should not happen for solvable states).")
        st.stop()

    solution_len = len(path) - 1

    st.markdown("### 📊 Results")
    c1, c2, c3 = st.columns(3)
    c1.metric("Solution length (moves)", solution_len)
    c2.metric("Nodes expanded", expanded)
    c3.metric("Search time (s)", f"{t1 - t0:.3f}")

    st.markdown("### ▶️ Step-by-step visualization")

    placeholder = st.empty()

    for step_idx, state in enumerate(path):
        g = step_idx
        h = h_misplaced(state, goal_state) if algo.startswith("A*") else None
        f = g + h if h is not None else None

        with placeholder.container():
            st.markdown(f"**Step {step_idx} / {solution_len}**")
            st.markdown(render_state_html(state), unsafe_allow_html=True)

            if algo.startswith("A*"):
                st.write(f"g(n) = {g}  (cost so far)")
                st.write(f"h(n) = {h}  (misplaced tiles)")
                st.write(f"f(n) = g(n) + h(n) = {f}")
            else:
                st.write(f"Depth = {g}")
                st.write("BFS has no heuristic: it explores level by level.")

        time.sleep(speed)

    st.success("Done! 🎉 Scroll up to try another configuration.")
