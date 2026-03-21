package eu.deknijf.docstoremobile.ui.screens.queue

import androidx.compose.foundation.Image
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
import androidx.compose.material.icons.automirrored.rounded.Logout
import androidx.compose.material.icons.automirrored.rounded.OpenInNew
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
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import eu.deknijf.docstoremobile.R
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
            .background(MaterialTheme.colorScheme.background),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            QueueMasthead(
                currentUser = currentUser,
                pending = pending,
                total = items.size,
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
                modifier = Modifier.padding(horizontal = 18.dp),
            )
        }

        if (pendingItems.isNotEmpty()) {
            item {
                QueueSectionHeader(
                    title = "Wachtrij",
                    count = pendingItems.size,
                    subtitle = "Deze scans of bestanden staan nog lokaal en worden pas verwijderd na een succesvolle upload.",
                    modifier = Modifier.padding(horizontal = 18.dp),
                )
            }
            items(pendingItems, key = { it.id }) { item ->
                QueueItemCard(item = item, onOpenDocument = onOpenDocument, modifier = Modifier.padding(horizontal = 18.dp))
            }
        }

        if (failedItems.isNotEmpty()) {
            item {
                QueueSectionHeader(
                    title = "Mislukt",
                    count = failedItems.size,
                    subtitle = "Backend of netwerk was niet bereikbaar. Deze bestanden blijven lokaal beschikbaar voor een nieuwe poging.",
                    modifier = Modifier.padding(horizontal = 18.dp),
                )
            }
            items(failedItems, key = { it.id }) { item ->
                QueueItemCard(item = item, onOpenDocument = onOpenDocument, modifier = Modifier.padding(horizontal = 18.dp))
            }
        }

        if (completeItems.isNotEmpty()) {
            item {
                QueueSectionHeader(
                    title = "Geüpload",
                    count = completeItems.size,
                    subtitle = "Deze items zijn al veilig doorgestuurd naar de webapp en kunnen daar verder beheerd worden.",
                    modifier = Modifier.padding(horizontal = 18.dp),
                )
            }
            items(completeItems, key = { it.id }) { item ->
                QueueItemCard(item = item, onOpenDocument = onOpenDocument, modifier = Modifier.padding(horizontal = 18.dp))
            }
        }

        if (items.isEmpty()) {
            item {
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 18.dp),
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
                            "De app houdt scans lokaal bij tot de upload bevestigd is. Je kan dus veilig scannen, ook als verbinding of backend tijdelijk wegvalt.",
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
        item { Spacer(modifier = Modifier.size(18.dp)) }
    }
}

@Composable
private fun QueueMasthead(
    currentUser: UserDto,
    pending: Int,
    total: Int,
    onBack: () -> Unit,
    onRetry: () -> Unit,
    onLogout: () -> Unit,
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.primary,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    Brush.verticalGradient(
                        listOf(
                            MaterialTheme.colorScheme.primary,
                            Color(0xFF254E8F),
                        ),
                    ),
                )
                .padding(horizontal = 18.dp, vertical = 22.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Surface(
                        shape = RoundedCornerShape(16.dp),
                        color = Color.White.copy(alpha = 0.10f),
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            IconButton(onClick = onBack, modifier = Modifier.size(34.dp)) {
                                Icon(Icons.AutoMirrored.Rounded.ArrowBack, contentDescription = "Terug", tint = Color.White)
                            }
                            Image(
                                painter = painterResource(R.drawable.docstore_logo),
                                contentDescription = "Docstore",
                                modifier = Modifier
                                    .size(34.dp)
                                    .clip(RoundedCornerShape(10.dp)),
                                contentScale = ContentScale.Fit,
                            )
                        }
                    }
                    Column {
                        Text(
                            "DOCUMENT CENTER",
                            style = MaterialTheme.typography.labelMedium,
                            color = Color.White.copy(alpha = 0.78f),
                            fontWeight = FontWeight.ExtraBold,
                        )
                        Text("Upload queue", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.ExtraBold, color = Color.White)
                        Text(
                            "Lokale scanbuffer voor ${currentUser.tenantName ?: "tenant"}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color.White.copy(alpha = 0.82f),
                        )
                    }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(2.dp), verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = onRetry) {
                        Icon(Icons.Rounded.Refresh, contentDescription = "Retry", tint = Color.White)
                    }
                    IconButton(onClick = onLogout) {
                        Icon(Icons.AutoMirrored.Rounded.Logout, contentDescription = "Logout", tint = Color.White)
                    }
                }
            }

            Surface(
                shape = RoundedCornerShape(18.dp),
                color = Color.White.copy(alpha = 0.08f),
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    SummaryTile("Wachtend", pending.toString(), listOf(Color(0xFFDCE8FF), Color(0xFFE8F0FF)), Modifier.weight(1f))
                    SummaryTile("Totaal", total.toString(), listOf(Color(0xFFE1F7EA), Color(0xFFEAFBF2)), Modifier.weight(1f))
                }
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
    modifier: Modifier = Modifier,
) {
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp,
        modifier = modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Text(
                "DOCUMENT CENTER",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontWeight = FontWeight.ExtraBold,
            )
            Text("Scanner-first uploadflow", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
            Text(
                "Zoals bij mobiele documentscanner-apps loopt alles eerst via een lokale buffer: scan, controle, bewaren en daarna asynchroon uploaden. Dat maakt de app veel betrouwbaarder dan een browserupload.",
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
                QueuePrimaryButton(
                    label = "Scan",
                    icon = Icons.Rounded.PhotoCamera,
                    colors = listOf(Color(0xFF2F8BFF), Color(0xFF48D3B3)),
                    modifier = Modifier.weight(1f),
                    onClick = onScanDocument,
                )
                QueuePrimaryButton(
                    label = "Bestand",
                    icon = Icons.Rounded.AddPhotoAlternate,
                    colors = listOf(Color(0xFF315FD4), Color(0xFF51C9B9)),
                    modifier = Modifier.weight(1f),
                    onClick = onImportFile,
                )
            }
            QueuePrimaryButton(
                label = "Nu opnieuw proberen",
                icon = Icons.Rounded.CloudUpload,
                colors = listOf(Color(0xFFDCE8FF), Color(0xFFE4FBF0)),
                modifier = Modifier.fillMaxWidth(),
                darkText = true,
                onClick = onRetry,
            )
            Text(
                "Queue-items blijven lokaal staan tot de backend de upload bevestigd heeft. Dat is dezelfde betrouwbaarheidsgedachte als bij scanner-apps, maar dan tenant-gebonden aan docstore.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun QueuePrimaryButton(
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    colors: List<Color>,
    modifier: Modifier = Modifier,
    darkText: Boolean = false,
    onClick: () -> Unit,
) {
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .clickable(onClick = onClick),
        color = Color.Transparent,
    ) {
        Box(
            modifier = Modifier
                .background(Brush.horizontalGradient(colors))
                .padding(horizontal = 16.dp, vertical = 14.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                val tint = if (darkText) MaterialTheme.colorScheme.onSurface else Color.White
                Icon(icon, contentDescription = null, tint = tint)
                Text(
                    " $label",
                    color = tint,
                    fontWeight = FontWeight.ExtraBold,
                )
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
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Text(
            "UPLOAD STATUS",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            fontWeight = FontWeight.ExtraBold,
        )
        Text("$title ($count)", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
        Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun QueueItemCard(
    item: PendingUploadEntity,
    onOpenDocument: (String) -> Unit,
    modifier: Modifier = Modifier,
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
        modifier = modifier.fillMaxWidth(),
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
                        maxLines = 1,
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
                    Text(" Open in webapp")
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
