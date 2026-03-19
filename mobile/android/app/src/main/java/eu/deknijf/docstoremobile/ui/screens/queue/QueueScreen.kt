package eu.deknijf.docstoremobile.ui.screens.queue

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.OpenInNew
import androidx.compose.material.icons.automirrored.rounded.Logout
import androidx.compose.material.icons.rounded.AddPhotoAlternate
import androidx.compose.material.icons.rounded.CloudDone
import androidx.compose.material.icons.rounded.CloudUpload
import androidx.compose.material.icons.rounded.ErrorOutline
import androidx.compose.material.icons.rounded.PhotoCamera
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material.icons.rounded.Schedule
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import eu.deknijf.docstoremobile.data.db.PendingUploadEntity
import eu.deknijf.docstoremobile.data.model.UploadStatus
import eu.deknijf.docstoremobile.data.model.UserDto
import eu.deknijf.docstoremobile.ui.viewmodel.DocumentsViewModel
import java.io.File
import java.text.DecimalFormat
import java.text.DecimalFormatSymbols
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun QueueScreen(
    viewModel: DocumentsViewModel,
    currentUser: UserDto,
    onLogout: () -> Unit,
    onRetry: () -> Unit,
    onScanDocument: () -> Unit,
    onImportFile: () -> Unit,
    onOpenDocument: (String) -> Unit,
    onBack: () -> Unit,
) {
    val items by viewModel.queueItems.collectAsStateWithLifecycle()
    val pending = items.count { it.status == UploadStatus.PENDING || it.status == UploadStatus.UPLOADING }
    val failed = items.count { it.status == UploadStatus.FAILED }
    val complete = items.count { it.status == UploadStatus.COMPLETE }
    val pendingItems = items.filter { it.status == UploadStatus.PENDING || it.status == UploadStatus.UPLOADING }
    val failedItems = items.filter { it.status == UploadStatus.FAILED }
    val completeItems = items.filter { it.status == UploadStatus.COMPLETE }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(horizontal = 18.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            QueueHero(
                currentUser = currentUser,
                onBack = onBack,
                onRetry = onRetry,
                onLogout = onLogout,
            )
        }
        item {
            QueueOverviewCard(
                pending = pending,
                failed = failed,
                complete = complete,
                onScanDocument = onScanDocument,
                onImportFile = onImportFile,
                onRetry = onRetry,
            )
        }

        if (pendingItems.isNotEmpty()) {
            item { QueueSectionHeader("Wachtrij", pendingItems.size, "Lokale scans en imports die nog moeten doorlopen.") }
            items(pendingItems, key = { it.id }) { item ->
                QueueItemCard(item = item, onOpenDocument = onOpenDocument)
            }
        }

        if (failedItems.isNotEmpty()) {
            item { QueueSectionHeader("Mislukt", failedItems.size, "Deze items bleven lokaal bewaard en kunnen opnieuw geprobeerd worden.") }
            items(failedItems, key = { it.id }) { item ->
                QueueItemCard(item = item, onOpenDocument = onOpenDocument)
            }
        }

        if (completeItems.isNotEmpty()) {
            item { QueueSectionHeader("Geüpload", completeItems.size, "Deze items staan al op de server en zijn lokaal vrijgegeven.") }
            items(completeItems, key = { it.id }) { item ->
                QueueItemCard(item = item, onOpenDocument = onOpenDocument)
            }
        }

        if (items.isEmpty()) {
            item {
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    color = MaterialTheme.colorScheme.surface,
                    tonalElevation = 2.dp,
                ) {
                    Column(
                        modifier = Modifier.padding(22.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        Text("Geen lokale uploads", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
                        Text(
                            "Nieuwe scans en bestanden worden eerst lokaal gecachet en daarna automatisch doorgestuurd naar Docstore.",
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            Button(onClick = onScanDocument, shape = RoundedCornerShape(16.dp)) {
                                Icon(Icons.Rounded.PhotoCamera, contentDescription = null)
                                Text(" Scan")
                            }
                            OutlinedButton(onClick = onImportFile, shape = RoundedCornerShape(16.dp)) {
                                Icon(Icons.Rounded.AddPhotoAlternate, contentDescription = null)
                                Text(" Bestand")
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun QueueHero(
    currentUser: UserDto,
    onBack: () -> Unit,
    onRetry: () -> Unit,
    onLogout: () -> Unit,
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
                Text("Upload queue", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.ExtraBold)
                Text(
                    currentUser.tenantName ?: "Tenant",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(2.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onRetry) {
                Icon(Icons.Rounded.Refresh, contentDescription = "Retry")
            }
            IconButton(onClick = onLogout) {
                Icon(Icons.AutoMirrored.Rounded.Logout, contentDescription = "Logout")
            }
        }
    }
}

@Composable
private fun QueueOverviewCard(
    pending: Int,
    failed: Int,
    complete: Int,
    onScanDocument: () -> Unit,
    onImportFile: () -> Unit,
    onRetry: () -> Unit,
) {
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Text("Lokale scanbuffer", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
            Text(
                "Elke scan of import wordt eerst lokaal bewaard. Als verbinding of backend tijdelijk wegvalt, blijft het bestand veilig op het toestel en probeert de app later opnieuw te uploaden.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                SummaryTile("Wachtrij", pending.toString(), listOf(Color(0xFFDCE8FF), Color(0xFFE8F0FF)), Modifier.weight(1f))
                SummaryTile("Mislukt", failed.toString(), listOf(Color(0xFFFFE3E5), Color(0xFFFFEEF0)), Modifier.weight(1f))
                SummaryTile("Klaar", complete.toString(), listOf(Color(0xFFE1F7EA), Color(0xFFEAFBF2)), Modifier.weight(1f))
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Button(
                    onClick = onScanDocument,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Icon(Icons.Rounded.PhotoCamera, contentDescription = null)
                    Text(" Scan")
                }
                OutlinedButton(
                    onClick = onImportFile,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Icon(Icons.Rounded.AddPhotoAlternate, contentDescription = null)
                    Text(" Bestand")
                }
            }
            Button(
                onClick = onRetry,
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(Icons.Rounded.CloudUpload, contentDescription = null)
                Text(" Retry uploads")
            }
        }
    }
}

@Composable
private fun SummaryTile(
    label: String,
    value: String,
    colors: List<Color>,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(18.dp),
        color = Color.Transparent,
    ) {
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(18.dp))
                .background(Brush.horizontalGradient(colors))
                .padding(14.dp),
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text(label, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(value, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
            }
        }
    }
}

@Composable
private fun QueueSectionHeader(
    title: String,
    count: Int,
    subtitle: String,
) {
    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Text("$title ($count)", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
        Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun QueueItemCard(
    item: PendingUploadEntity,
    onOpenDocument: (String) -> Unit,
) {
    val localState = when {
        item.status == UploadStatus.COMPLETE -> "Lokaal bestand vrijgegeven na upload"
        File(item.localPath).exists() -> "Lokaal gecachet op toestel"
        else -> "Lokale cache niet meer beschikbaar"
    }

    Surface(
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(22.dp),
        tonalElevation = 2.dp,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top,
            ) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(
                        item.displayName,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.ExtraBold,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        "${mimeLabel(item.mimeType)} · ${formatFileSize(item.sizeBytes)}",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
                QueueStatusBadge(item.status)
            }

            DetailInfoRow("Aangemaakt", formatDateTime(item.createdAt))
            DetailInfoRow("Laatste update", formatDateTime(item.updatedAt))
            DetailInfoRow("Opslag", localState)
            DetailInfoRow("Pogingen", item.attemptCount.toString())

            if (!item.lastError.isNullOrBlank()) {
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = MaterialTheme.colorScheme.error.copy(alpha = 0.10f),
                ) {
                    Text(
                        item.lastError,
                        modifier = Modifier.padding(12.dp),
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }

            item.serverDocumentId?.let { docId ->
                OutlinedButton(
                    onClick = { onOpenDocument(docId) },
                    shape = RoundedCornerShape(16.dp),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Icon(Icons.AutoMirrored.Rounded.OpenInNew, contentDescription = null)
                    Text(" Document openen")
                }
            }
        }
    }
}

@Composable
private fun DetailInfoRow(
    label: String,
    value: String,
) {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.surfaceVariant,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(label, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(
                value,
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.SemiBold,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun QueueStatusBadge(status: UploadStatus) {
    val (label, colors, icon) = when (status) {
        UploadStatus.PENDING -> Triple("Wachtend", listOf(Color(0xFFDCE8FF), Color(0xFFE9F1FF)), Icons.Rounded.Schedule)
        UploadStatus.UPLOADING -> Triple("Uploading", listOf(Color(0xFFFDF1CF), Color(0xFFFFF7DE)), Icons.Rounded.CloudUpload)
        UploadStatus.FAILED -> Triple("Mislukt", listOf(Color(0xFFFFE3E5), Color(0xFFFFEEF0)), Icons.Rounded.ErrorOutline)
        UploadStatus.COMPLETE -> Triple("Geüpload", listOf(Color(0xFFE1F7EA), Color(0xFFEAFBF2)), Icons.Rounded.CloudDone)
    }
    Surface(shape = RoundedCornerShape(999.dp), color = Color.Transparent) {
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(999.dp))
                .background(Brush.horizontalGradient(colors))
                .padding(horizontal = 10.dp, vertical = 6.dp),
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(icon, contentDescription = null, modifier = Modifier.size(16.dp))
                Text(label, style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.ExtraBold)
            }
        }
    }
}

private fun formatDateTime(epochMillis: Long): String {
    return SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault()).format(Date(epochMillis))
}

private fun formatFileSize(bytes: Long): String {
    if (bytes <= 0L) return "0 B"
    val units = arrayOf("B", "KB", "MB", "GB")
    var value = bytes.toDouble()
    var index = 0
    while (value >= 1024 && index < units.lastIndex) {
        value /= 1024.0
        index += 1
    }
    val symbols = DecimalFormatSymbols(Locale.US).apply { decimalSeparator = ',' }
    val formatter = DecimalFormat(if (value >= 100 || index == 0) "0" else "0.0", symbols)
    return "${formatter.format(value)} ${units[index]}"
}

private fun mimeLabel(mimeType: String): String {
    return when {
        mimeType.equals("application/pdf", ignoreCase = true) -> "PDF"
        mimeType.startsWith("image/", ignoreCase = true) -> "Afbeelding"
        else -> "Bestand"
    }
}
