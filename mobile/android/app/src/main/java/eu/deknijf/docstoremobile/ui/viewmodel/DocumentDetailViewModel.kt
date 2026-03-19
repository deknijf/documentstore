package eu.deknijf.docstoremobile.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import eu.deknijf.docstoremobile.data.model.DocumentDto
import eu.deknijf.docstoremobile.data.repository.DocumentsRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class DocumentDetailUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val document: DocumentDto? = null,
)

class DocumentDetailViewModel(
    private val documentId: String,
    private val tokenProvider: suspend () -> String?,
    private val documentsRepository: DocumentsRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow(DocumentDetailUiState(loading = true))
    val uiState: StateFlow<DocumentDetailUiState> = _uiState.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            val token = tokenProvider().orEmpty()
            if (token.isBlank()) {
                _uiState.value = DocumentDetailUiState(error = "Geen actieve sessie")
                return@launch
            }
            _uiState.value = DocumentDetailUiState(loading = true)
            runCatching { documentsRepository.getDocument(token, documentId) }
                .onSuccess { doc -> _uiState.value = DocumentDetailUiState(document = doc) }
                .onFailure { ex -> _uiState.value = DocumentDetailUiState(error = ex.message ?: "Kan document niet laden") }
        }
    }
}
