package eu.deknijf.docstoremobile.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class LoginRequest(
    val email: String,
    val password: String,
)

@Serializable
data class UserDto(
    val id: String,
    @SerialName("tenant_id") val tenantId: String,
    @SerialName("tenant_name") val tenantName: String? = null,
    val email: String,
    val name: String,
    @SerialName("avatar_path") val avatarPath: String? = null,
    val role: String = "gebruiker",
    @SerialName("is_bootstrap_admin") val isBootstrapAdmin: Boolean = false,
    @SerialName("is_admin") val isAdmin: Boolean = false,
)

@Serializable
data class AuthResponse(
    val token: String,
    val user: UserDto,
)
