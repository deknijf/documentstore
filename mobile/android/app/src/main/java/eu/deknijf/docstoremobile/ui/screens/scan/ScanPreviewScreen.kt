package eu.deknijf.docstoremobile.ui.screens.scan

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.PhotoCamera
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import eu.deknijf.docstoremobile.data.model.UserDto
import java.io.File
import java.text.DecimalFormat
import java.text.DecimalFormatSymbols
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun ScanPreviewScreen(
    currentUser: UserDto,
    pages: List<File>,
    draftCreatedAt: Long,
    onBack: () -> Unit,
    onRescan: () -> Unit,
    onAddPage: () -> Unit,
    onSave: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(horizontal = 18.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            PreviewHero(
                currentUser = currentUser,
                pageCount = pages.size,
                draftCreatedAt = draftCreatedAt,
                onBack = onBack,
                onRescan = onRescan,
            )
        }
        item {
            PreviewInfoCard(
                pageCount = pages.size,
                onAddPage = onAddPage,
                onSave = onSave,
            )
        }
        itemsIndexed(pages, key = { _, file -> file.absolutePath }) { index, file ->
            PreviewPageCard(
                pageNumber = index + 1,
                totalPages = pages.size,
                file = file,
            )
        }
        item { Spacer(modifier = Modifier.height(18.dp)) }
    }
}

@Composable
private fun PreviewHero(
    currentUser: UserDto,
    pageCount: Int,
    draftCreatedAt: Long,
    onBack: () -> Unit,
    onRescan: () -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Rounded.ArrowBack, contentDescription = "Terug")
            }
            Column {
                Text("Scan preview", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.ExtraBold)
                Text(
                    "${currentUser.tenantName ?: "Tenant"} · $pageCount pagina${if (pageCount == 1) "" else "'s"} · ${formatPreviewTimestamp(draftCreatedAt)}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        OutlinedButton(onClick = onRescan, shape = RoundedCornerShape(16.dp)) {
            Icon(Icons.Rounded.PhotoCamera, contentDescription = null)
            Text(" Opnieuw")
        }
    }
}

@Composable
private fun PreviewInfoCard(
    pageCount: Int,
    onAddPage: () -> Unit,
    onSave: () -> Unit,
) {
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text("Controleer de scan eerst", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
            Text(
                "De scan staat nog niet in de uploadqueue. Bekijk eerst alle pagina's, voeg indien nodig nog een extra pagina toe en bewaar pas daarna de definitieve PDF.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                OutlinedButton(
                    onClick = onAddPage,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Icon(Icons.Rounded.Add, contentDescription = null)
                    Text(" Extra pagina")
                }
                Button(
                    onClick = onSave,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Icon(Icons.Rounded.CheckCircle, contentDescription = null)
                    Text(" Bewaren")
                }
            }
            Text(
                "Opslaan maakt één lokale PDF van ${pageCount.toString()} pagina${if (pageCount == 1) "" else "'s"} en zet die daarna in de uploadqueue.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun PreviewPageCard(
    pageNumber: Int,
    totalPages: Int,
    file: File,
) {
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Pagina $pageNumber", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.ExtraBold)
                Text(
                    "van $totalPages · ${formatFileSize(file.length())}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Surface(
                shape = RoundedCornerShape(18.dp),
                color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f),
                modifier = Modifier.fillMaxWidth(),
            ) {
                AsyncImage(
                    model = file,
                    contentDescription = "Scanpagina $pageNumber",
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(18.dp)),
                    contentScale = ContentScale.FillWidth,
                )
            }
            Surface(
                shape = RoundedCornerShape(999.dp),
                color = MaterialTheme.colorScheme.primary.copy(alpha = 0.10f),
            ) {
                Text(
                    text = file.name,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
            }
        }
    }
}

private fun formatPreviewTimestamp(value: Long): String {
    return SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault()).format(Date(value))
}

private fun formatFileSize(sizeBytes: Long): String {
    val symbols = DecimalFormatSymbols(Locale.US).apply { decimalSeparator = '.' }
    val decimal = DecimalFormat("0.0", symbols)
    val kb = sizeBytes / 1024.0
    val mb = kb / 1024.0
    return if (mb >= 1.0) "${decimal.format(mb)} MB" else "${decimal.format(kb)} KB"
}
