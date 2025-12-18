from typing import List, Dict, Optional
from final.rag.vector_store import ChromaVectorStore
from final.rag.progress_view import build_chunk_progress_note


class ContentRetriever:
    """Recupera contenido relevante usando RAG."""

    def __init__(self, vector_store: ChromaVectorStore):
        self.vector_store = vector_store

    def retrieve_relevant_content(
        self,
        query: str,
        n_results: int = 3,
        min_similarity: float = 0.5
    ) -> str:
        """
        Recupera contenido relevante para una query.

        Args:
            query: Texto de búsqueda
            n_results: Número de fragmentos a recuperar
            min_similarity: Umbral mínimo de similitud (no usado actualmente)

        Returns:
            Contenido formateado con los fragmentos más relevantes
        """
        if not query:
            return "No se proporcionó una query válida."

        buffer = 8
        results = self.vector_store.query(query, n_results=max(n_results + buffer, n_results))

        if not results.get('documents') or not results['documents'][0]:
            return "No se encontró contenido relevante."

        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0] or [None] * len(docs)

        candidates = list(zip(ids, docs, metadatas))
        selected = self._filter_mastered_chunks(candidates, n_results)

        formatted_content = []
        for i, (chunk_id, doc, metadata) in enumerate(selected, start=1):
            chunk_index = metadata.get("chunk_index")
            subtopics = metadata.get("subtopics", [])
            progress_note = build_chunk_progress_note(str(chunk_id)) if chunk_id else "chunk_status=unknown"
            formatted_content.append(
                "\n".join(
                    [
                        f"[Fragmento {i}]",
                        f"chunk_id: {chunk_id}",
                        f"chunk_index: {chunk_index}",
                        f"subtopics: {subtopics}",
                        f"progress: {progress_note}",
                        f"{doc}",
                        "",
                    ]
                )
            )

        return "\n".join(formatted_content)

    def _filter_mastered_chunks(self, candidates: List[tuple], n_results: int) -> List[tuple]:
        kept: List[tuple] = []
        deferred: List[tuple] = []
        for chunk_id, doc, metadata in candidates:
            if not chunk_id:
                kept.append((chunk_id, doc, metadata))
                continue
            note = build_chunk_progress_note(str(chunk_id))
            if "chunk_status=mastered" in note:
                deferred.append((chunk_id, doc, metadata))
            else:
                kept.append((chunk_id, doc, metadata))

        selected = kept[:n_results]
        if len(selected) < n_results:
            selected.extend(deferred[: (n_results - len(selected))])
        return selected

    def retrieve_for_question_creation(
        self,
        topic: Optional[str] = None,
        difficulty_hint: Optional[str] = None,
        n_results: int = 3
    ) -> str:
        """
        Recupera contenido específico para crear una pregunta.

        Args:
            topic: Tema específico (opcional)
            difficulty_hint: Hint sobre dificultad deseada (opcional)
            n_results: Número de fragmentos a recuperar

        Returns:
            Contenido formateado para crear pregunta
        """
        if topic:
            query = f"Explica conceptos sobre {topic}"
        else:
            query = "Conceptos importantes del curso"

        if difficulty_hint:
            query += f" {difficulty_hint}"

        return self.retrieve_relevant_content(query, n_results)

    def retrieve_related_to_errors(
        self,
        incorrect_questions: List[str],
        n_results: int = 5
    ) -> str:
        """
        Recupera contenido relacionado a preguntas que el usuario respondió incorrectamente.

        Args:
            incorrect_questions: Lista de preguntas incorrectas
            n_results: Número de fragmentos a recuperar

        Returns:
            Contenido relacionado a los errores del usuario
        """
        if not incorrect_questions:
            return "No hay preguntas incorrectas para analizar."

        # Combinar preguntas incorrectas en una query (limitar a 3)
        query = " ".join(incorrect_questions[:3])

        content = self.retrieve_relevant_content(query, n_results)

        # Agregar contexto adicional
        header = f"Contenido relacionado a {len(incorrect_questions)} pregunta(s) incorrecta(s):\n\n"
        return header + content

    def retrieve_diverse_content(
        self,
        n_samples: int = 5,
        previously_covered: Optional[List[str]] = None
    ) -> List[str]:
        """
        Recupera contenido diverso para evitar repetición de temas.

        Args:
            n_samples: Número de fragmentos diversos a recuperar
            previously_covered: Lista de temas ya cubiertos (opcional)

        Returns:
            Lista de fragmentos de contenido
        """
        # Para diversidad, hacer queries sobre diferentes aspectos generales
        queries = [
            "conceptos fundamentales",
            "aplicaciones prácticas",
            "casos de uso",
            "definiciones importantes",
            "ejemplos y ejercicios"
        ]

        all_content = []
        for query in queries[:n_samples]:
            results = self.vector_store.query(query, n_results=1)
            if results['documents'][0]:
                all_content.append(results['documents'][0][0])

        return all_content

    def search_specific_concept(
        self,
        concept: str,
        n_results: int = 2
    ) -> str:
        """
        Busca información sobre un concepto específico.

        Args:
            concept: Concepto a buscar
            n_results: Número de resultados

        Returns:
            Contenido sobre el concepto
        """
        query = f"Definición y explicación de {concept}"
        return self.retrieve_relevant_content(query, n_results)
