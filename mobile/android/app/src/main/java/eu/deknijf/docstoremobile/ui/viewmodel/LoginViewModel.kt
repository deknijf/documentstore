package eu.deknijf.docstoremobile.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import eu.deknijf.docstoremobile.data.model.UserDto
import eu.deknijf.docstoremobile.data.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class LoginUiState(
    val login: String = "",
    val password: String = "",
    val loading: Boolean = false,
    val error: String? = null,
    val user: UserDto? = null,
)

class LoginViewModel(private val authRepository: AuthRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    fun updateLogin(value: String) {
        _uiState.value = _uiState.value.copy(login = value, error = null)
    }

    fun updatePassword(value: String) {
        _uiState.value = _uiState.value.copy(password = value, error = null)
    }

    fun login() {
        val current = _uiState.value
        if (current.login.isBlank() || current.password.isBlank()) {
            _uiState.value = current.copy(error = "Login en wachtwoord zijn verplicht")
            return
        }
        viewModelScope.launch {
            _uiState.value = current.copy(loading = true, error = null)
            authRepository.login(current.login, current.password)
                .onSuccess { user ->
                    _uiState.value = _uiState.value.copy(loading = false, user = user)
                }
                .onFailure { ex ->
                    _uiState.value = _uiState.value.copy(loading = false, error = ex.message ?: "Login mislukt")
                }
        }
    }
}
