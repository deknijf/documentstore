package eu.deknijf.docstoremobile.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightScheme = lightColorScheme(
    primary = Color(0xFF2F69D9),
    onPrimary = Color.White,
    secondary = Color(0xFF4DD1B0),
    tertiary = Color(0xFFDCE8FB),
    background = Color(0xFFF4F8FF),
    surface = Color(0xFFFFFFFF),
    surfaceVariant = Color(0xFFEDF4FF),
    onSurface = Color(0xFF19335E),
    onBackground = Color(0xFF19335E),
    onSurfaceVariant = Color(0xFF5F7294),
    outline = Color(0xFFBDD1F2),
    error = Color(0xFFD85168),
)

@Composable
fun DocstoreTheme(
    darkTheme: Boolean = false,
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = LightScheme,
        content = content,
    )
}
