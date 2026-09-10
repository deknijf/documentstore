package eu.deknijf.docstoremobile.data.api

import okhttp3.Interceptor
import okhttp3.Response
import java.net.HttpURLConnection

/**
 * Reacts to the server rejecting our session token.
 *
 * Without this the app kept a dead token forever: uploads failed with 401 every
 * fifteen minutes, the document list stayed empty, and nothing ever brought the
 * user back to the login screen.
 */
class UnauthorizedInterceptor(
    private val onUnauthorized: () -> Unit,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val response = chain.proceed(request)
        // A wrong password answers 401 as well; that is a failed login, not an
        // expired session, so it must not clear anything.
        if (response.code == HttpURLConnection.HTTP_UNAUTHORIZED && !request.isLogin()) {
            onUnauthorized()
        }
        return response
    }

    private fun okhttp3.Request.isLogin(): Boolean = url.encodedPath.endsWith("/api/auth/login")
}
