package eu.deknijf.docstoremobile.data.api

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import eu.deknijf.docstoremobile.data.model.UserDto
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

private val Context.sessionDataStore by preferencesDataStore(name = "docstore_session")

class SessionStore(private val context: Context) {
    private val json = Json { ignoreUnknownKeys = true; explicitNulls = false }

    private val tokenKey = stringPreferencesKey("token")
    private val userKey = stringPreferencesKey("user_json")

    val tokenFlow: Flow<String?> = context.sessionDataStore.data.map { it[tokenKey] }
    val userFlow: Flow<UserDto?> = context.sessionDataStore.data.map { prefs ->
        prefs[userKey]?.let {
            runCatching { json.decodeFromString<UserDto>(it) }.getOrNull()
        }
    }

    suspend fun saveSession(token: String, user: UserDto) {
        context.sessionDataStore.edit {
            it[tokenKey] = token
            it[userKey] = json.encodeToString(user)
        }
    }

    suspend fun clearSession() {
        context.sessionDataStore.edit {
            it.remove(tokenKey)
            it.remove(userKey)
        }
    }
}
