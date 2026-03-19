package eu.deknijf.docstoremobile.data.repository

import eu.deknijf.docstoremobile.data.api.DocstoreApi
import eu.deknijf.docstoremobile.data.api.SessionStore
import eu.deknijf.docstoremobile.data.model.LoginRequest
import eu.deknijf.docstoremobile.data.model.UserDto
import kotlinx.coroutines.flow.Flow

class AuthRepository(
    private val api: DocstoreApi,
    private val sessionStore: SessionStore,
) {
    val sessionUser: Flow<UserDto?> = sessionStore.userFlow
    val sessionToken: Flow<String?> = sessionStore.tokenFlow

    suspend fun login(login: String, password: String): Result<UserDto> {
        return runCatching {
            val auth = api.login(LoginRequest(email = login.trim(), password = password))
            sessionStore.saveSession(auth.token, auth.user)
            auth.user
        }
    }

    suspend fun refreshMe(token: String): Result<UserDto> {
        return runCatching {
            val user = api.me("Bearer $token")
            sessionStore.saveSession(token, user)
            user
        }
    }

    suspend fun logout() {
        sessionStore.clearSession()
    }
}
