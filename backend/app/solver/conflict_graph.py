from typing import Dict, List, Set, Tuple
from collections import defaultdict

class ExamConflictGraph:
    """
    Examination Conflict Graph:
    Vertices: Course Examinations
    Edges: Connect two examinations that share at least one student.
    Edge weight: Number of shared enrolled students.
    """
    def __init__(self, exam_ids: List[int], exam_enrollments: Dict[int, Set[int]]):
        """
        :param exam_ids: List of exam IDs
        :param exam_enrollments: Dict mapping exam_id -> set of student_ids
        """
        self.exam_ids: List[int] = list(exam_ids)
        self.exam_enrollments: Dict[int, Set[int]] = exam_enrollments
        self.adj: Dict[int, Set[int]] = defaultdict(set)
        self.shared_counts: Dict[Tuple[int, int], int] = {}
        self.student_to_exams: Dict[int, Set[int]] = defaultdict(set)

        self._build_graph()

    def _build_graph(self):
        # Inverted index: student -> exams
        for e_id in self.exam_ids:
            for s_id in self.exam_enrollments.get(e_id, set()):
                self.student_to_exams[s_id].add(e_id)

        # Build edges based on shared students
        for s_id, exams in self.student_to_exams.items():
            exam_list = list(exams)
            n = len(exam_list)
            for i in range(n):
                for j in range(i + 1, n):
                    u, v = exam_list[i], exam_list[j]
                    self.adj[u].add(v)
                    self.adj[v].add(u)
                    pair = (min(u, v), max(u, v))
                    self.shared_counts[pair] = self.shared_counts.get(pair, 0) + 1

    def has_conflict(self, exam_u: int, exam_v: int) -> bool:
        return exam_v in self.adj.get(exam_u, set())

    def get_shared_student_count(self, exam_u: int, exam_v: int) -> int:
        pair = (min(u, v), max(u, v)) if (u := exam_u) and (v := exam_v) else (0, 0)
        return self.shared_counts.get(pair, 0)

    def get_shared_students(self, exam_u: int, exam_v: int) -> Set[int]:
        return self.exam_enrollments.get(exam_u, set()).intersection(
            self.exam_enrollments.get(exam_v, set())
        )

    def get_degree(self, exam_id: int) -> int:
        return len(self.adj.get(exam_id, set()))

    def get_weighted_degree(self, exam_id: int) -> int:
        """Sum of shared students across all adjacent conflicting exams."""
        total = 0
        for neighbor in self.adj.get(exam_id, set()):
            total += self.get_shared_student_count(exam_id, neighbor)
        return total

    def degree_ordered_exams(self) -> List[int]:
        """Order examinations by descending conflict degree (Welsh-Powell heuristic)."""
        return sorted(self.exam_ids, key=lambda e: (self.get_degree(e), len(self.exam_enrollments.get(e, set()))), reverse=True)

    def estimate_min_slots_clique(self) -> int:
        """
        Greedy maximum clique estimation:
        Provides a valid lower bound on the number of time slots required.
        Since any clique in the conflict graph requires mutually distinct slots,
        chromatic number >= clique number.
        """
        if not self.exam_ids:
            return 0
        sorted_nodes = self.degree_ordered_exams()
        max_clique_size = 1

        # Check largest degree nodes
        for start_node in sorted_nodes[:15]:
            clique = [start_node]
            candidates = set(self.adj.get(start_node, set()))
            for cand in sorted(candidates, key=lambda x: self.get_degree(x), reverse=True):
                # Is cand connected to all current members of clique?
                if all(cand in self.adj.get(member, set()) for member in clique):
                    clique.append(cand)
            if len(clique) > max_clique_size:
                max_clique_size = len(clique)

        return max_clique_size

    def get_density(self) -> float:
        n = len(self.exam_ids)
        if n < 2:
            return 0.0
        total_possible = n * (n - 1) / 2
        total_edges = sum(len(neighbors) for neighbors in self.adj.values()) / 2
        return total_edges / total_possible
