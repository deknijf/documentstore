@file:OptIn(ExperimentalLayoutApi::class)

package eu.deknijf.docstoremobile.ui.screens.documents

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.Logout
import androidx.compose.material.icons.rounded.AddPhotoAlternate
import androidx.compose.material.icons.rounded.CloudUpload
import androidx.compose.material.icons.rounded.PhotoCamera
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedAssistChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import coil.request.ImageRequest
import eu.deknijf.docstoremobile.BuildConfig
import eu.deknijf.docstoremobile.R
import eu.deknijf.docstoremobile.data.db.PendingUploadEntity
import eu.deknijf.docstoremobile.data.model.DocumentDto
import eu.deknijf.docstoremobile.data.model.UserDto
import eu.deknijf.docstoremobile.ui.viewmodel.DocumentsViewModel
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException
import java.util.Locale

@Composable
fun DocumentsScreen(
    viewModel: DocumentsViewModel,
    snackbarHostState: SnackbarHostState,
    currentUser: UserDto,
    onOpenDocument: (String) -> Unit,
    onOpenQueue: () -> Unit,
    onScanDocument: () -> Unit,
    onImportFile: () -> Unit,
    onLogout: () -> Unit,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val queueSummary by viewModel.queueSummary.collectAsStateWithLifecycle()
    val queueItems by viewModel.queueItems.collectAsStateWithLifecycle()

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            item {
                DocumentsHero(
                    user = currentUser,
                    pendingCount = queueSummary.pendingCount,
                    totalQueued = queueItems.size,
                    onRefresh = viewModel::refresh,
                    onOpenQueue = onOpenQueue,
                    onLogout = onLogout,
                )
            }
            item {
                ActionRow(
                    onScanDocument = onScanDocument,
                    onImportFile = onImportFile,
                    onOpenQueue = onOpenQueue,
                )
            }
            item {
                UploadFlowCard(
                    modifier = Modifier.padding(horizontal = 18.dp),
                    pendingCount = queueSummary.pendingCount,
                    totalQueued = queueItems.size,
                )
            }
            if (state.loading) {
                item {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 18.dp),
                        horizontalArrangement = Arrangement.Center,
                    ) {
                        CircularProgressIndicator()
                    }
                }
            }
            state.error?.let { error ->
                item {
                    Surface(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 18.dp),
                        color = MaterialTheme.colorScheme.error.copy(alpha = 0.12f),
                        shape = RoundedCornerShape(18.dp),
                    ) {
                        Text(
                            text = error,
                            modifier = Modifier.padding(16.dp),
                            color = MaterialTheme.colorScheme.error,
                        )
                    }
                }
            }
            if (queueItems.isNotEmpty()) {
                item {
                    PendingUploadsStrip(
                        items = queueItems,
                        modifier = Modifier.padding(horizontal = 18.dp),
                        onOpenQueue = onOpenQueue,
                    )
                }
            }
            item {
                Text(
                    text = "Documenten",
                    modifier = Modifier.padding(horizontal = 18.dp),
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                )
            }
            items(state.documents, key = { it.id }) { document ->
                DocumentCard(
                    document = document,
                    modifier = Modifier.padding(horizontal = 18.dp),
                    onOpen = { onOpenDocument(document.id) },
                )
            }
            item { Spacer(modifier = Modifier.height(18.dp)) }
        }
    }
}

@Composable
private fun DocumentsHero(
    user: UserDto,
    pendingCount: Int,
    totalQueued: Int,
    onRefresh: () -> Unit,
    onOpenQueue: () -> Unit,
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
                            MaterialTheme.colorScheme.primary.copy(alpha = 0.92f),
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
                    Image(
                        painter = painterResource(R.drawable.docstore_logo),
                        contentDescription = "Docstore",
                        modifier = Modifier
                            .size(54.dp)
                            .clip(RoundedCornerShape(14.dp)),
                    )
                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(
                            text = "docstore",
                            color = MaterialTheme.colorScheme.onPrimary,
                            style = MaterialTheme.typography.headlineSmall,
                            fontWeight = FontWeight.ExtraBold,
                        )
                        Text(
                            text = user.tenantName?.takeIf { it.isNotBlank() } ?: "Tenant",
                            color = MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.82f),
                            style = MaterialTheme.typography.bodyMedium,
                        )
                    }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(4.dp), verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = onRefresh) {
                        Icon(Icons.Rounded.Refresh, contentDescription = "Refresh", tint = MaterialTheme.colorScheme.onPrimary)
                    }
                    IconButton(onClick = onLogout) {
                        Icon(Icons.AutoMirrored.Rounded.Logout, contentDescription = "Logout", tint = MaterialTheme.colorScheme.onPrimary)
                    }
                }
            }

            FlowRow(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                ElevatedAssistChip(
                    onClick = onOpenQueue,
                    label = { Text("${user.name.take(24)}") },
                    leadingIcon = { Icon(Icons.Rounded.CloudUpload, contentDescription = null) },
                )
                ElevatedAssistChip(
                    onClick = onOpenQueue,
                    label = { Text("Queue $pendingCount/$totalQueued") },
                    leadingIcon = { Icon(Icons.Rounded.CloudUpload, contentDescription = null) },
                )
                if (user.role.equals("superadmin", true)) {
                    StatusBadge(label = "Superadmin", tint = listOf(0xFF7C68F6, 0xFFA56CFF))
                } else if (user.role.equals("admin", true)) {
                    StatusBadge(label = "Admin", tint = listOf(0xFF2F69D9, 0xFF4DD1B0))
                }
            }
        }
    }
}

@Composable
private fun ActionRow(
    onScanDocument: () -> Unit,
    onImportFile: () -> Unit,
    onOpenQueue: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 18.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Button(
            onClick = onScanDocument,
            modifier = Modifier.weight(1f),
            shape = RoundedCornerShape(18.dp),
        ) {
            Icon(Icons.Rounded.PhotoCamera, contentDescription = null)
            Spacer(modifier = Modifier.size(8.dp))
            Text("Scan")
        }
        Button(
            onClick = onImportFile,
            modifier = Modifier.weight(1f),
            shape = RoundedCornerShape(18.dp),
        ) {
            Icon(Icons.Rounded.AddPhotoAlternate, contentDescription = null)
            Spacer(modifier = Modifier.size(8.dp))
            Text("Bestand")
        }
        Button(
            onClick = onOpenQueue,
            modifier = Modifier.weight(1f),
            shape = RoundedCornerShape(18.dp),
        ) {
            Icon(Icons.Rounded.CloudUpload, contentDescription = null)
            Spacer(modifier = Modifier.size(8.dp))
            Text("Queue")
        }
    }
}

@Composable
private fun UploadFlowCard(
    pendingCount: Int,
    totalQueued: Int,
    modifier: Modifier = Modifier,
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp,
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Upload flow", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.ExtraBold)
            Text(
                text = "Nieuwe scans en bestanden worden eerst lokaal gecachet. Daarna uploadt de app automatisch naar Docstore en blijft de queue retry-safe als netwerk of backend tijdelijk wegvalt.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (totalQueued > 0) {
                Text(
                    text = "Queue status: $pendingCount wachtend van $totalQueued lokaal opgeslagen item(s).",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onSurface,
                    fontWeight = FontWeight.SemiBold,
                )
            }
        }
    }
}

@Composable
private fun PendingUploadsStrip(
    items: List<PendingUploadEntity>,
    modifier: Modifier = Modifier,
    onOpenQueue: () -> Unit,
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onOpenQueue),
        color = MaterialTheme.colorScheme.surfaceVariant,
        shape = RoundedCornerShape(20.dp),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Lokale upload-queue", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            items.take(3).forEach { item ->
                Text("• ${item.displayName} · ${item.status.name.lowercase()}", color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            if (items.size > 3) {
                Text("+ ${items.size - 3} extra", color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@Composable
private fun DocumentCard(
    document: DocumentDto,
    modifier: Modifier = Modifier,
    onOpen: () -> Unit,
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onOpen),
        shape = RoundedCornerShape(22.dp),
        tonalElevation = 2.dp,
        color = MaterialTheme.colorScheme.surface,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(0.dp)) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(180.dp)
                    .background(MaterialTheme.colorScheme.surfaceVariant),
            ) {
                val thumbnailUrl = document.thumbnailPath?.let {
                    "${BuildConfig.DOCSTORE_BASE_URL.trimEnd('/')}$it?v=${document.updatedAt}"
                }
                if (thumbnailUrl != null) {
                    AsyncImage(
                        model = ImageRequest.Builder(androidx.compose.ui.platform.LocalContext.current)
                            .data(thumbnailUrl)
                            .crossfade(true)
                            .build(),
                        contentDescription = document.subject ?: document.filename,
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Crop,
                    )
                }
                Column(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(10.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                    horizontalAlignment = Alignment.End,
                ) {
                    if (document.ocrProcessed) StatusBadge("OCR")
                    if (document.aiProcessed) StatusBadge("AI")
                    if (document.bankPaidVerified || document.paid) StatusBadge("PAID", tint = listOf(0xFF7965F4, 0xFF9B79FF))
                }
                if (document.labelNames.isNotEmpty()) {
                    Surface(
                        modifier = Modifier
                            .align(Alignment.BottomStart)
                            .padding(10.dp),
                        shape = RoundedCornerShape(999.dp),
                        color = MaterialTheme.colorScheme.surface.copy(alpha = 0.96f),
                    ) {
                        Text(
                            text = document.labelNames.first(),
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                            style = MaterialTheme.typography.labelLarge,
                            fontWeight = FontWeight.Bold,
                        )
                    }
                }
            }
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text(
                    text = document.issuer ?: "Onbekende afzender",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.ExtraBold,
                )
                Text(
                    text = document.subject ?: document.filename,
                    style = MaterialTheme.typography.bodyLarge,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                FlowRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    document.category?.let { MiniPill(it) }
                    MiniPill(formatDate(document.documentDate) ?: "Geen documentdatum")
                    document.totalAmount?.let {
                        MiniPill("${formatMoney(it)} ${document.currency ?: "EUR"}")
                    }
                }
            }
        }
    }
}

@Composable
private fun StatusBadge(
    label: String,
    tint: List<Long> = listOf(0xFFDAF4E8, 0xFFE8F9EF),
) {
    Surface(
        shape = RoundedCornerShape(999.dp),
        color = androidx.compose.ui.graphics.Color(tint.first()),
    ) {
        Text(
            text = label,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp),
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.ExtraBold,
            color = MaterialTheme.colorScheme.onSurface,
        )
    }
}

@Composable
private fun MiniPill(value: String) {
    Surface(
        shape = RoundedCornerShape(999.dp),
        color = MaterialTheme.colorScheme.surfaceVariant,
    ) {
        Text(
            text = value,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
    }
}

private fun formatDate(raw: String?): String? {
    val value = raw?.trim().orEmpty()
    if (value.isBlank()) return null
    return runCatching {
        LocalDate.parse(value).format(DateTimeFormatter.ofPattern("dd/MM/yyyy", Locale.getDefault()))
    }.getOrElse {
        try {
            LocalDate.parse(value.substring(0, 10)).format(DateTimeFormatter.ofPattern("dd/MM/yyyy", Locale.getDefault()))
        } catch (_: DateTimeParseException) {
            value
        }
    }
}

private fun formatMoney(amount: Double): String {
    return String.format(Locale.US, "%.2f", amount).replace('.', ',')
}
