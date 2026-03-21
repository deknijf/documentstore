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
import androidx.compose.material.icons.automirrored.rounded.OpenInNew
import androidx.compose.material.icons.rounded.AddPhotoAlternate
import androidx.compose.material.icons.rounded.CloudUpload
import androidx.compose.material.icons.rounded.PhotoCamera
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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
import androidx.compose.ui.graphics.Color
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
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            item {
                UploadMasthead(
                    currentUser = currentUser,
                    pendingCount = queueSummary.pendingCount,
                    totalQueued = queueItems.size,
                    onRefresh = viewModel::refresh,
                    onLogout = onLogout,
                )
            }
            item {
                UploadPrimaryActions(
                    modifier = Modifier.padding(horizontal = 18.dp),
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
            if (queueItems.isNotEmpty()) {
                item {
                    PendingUploadsStrip(
                        items = queueItems,
                        modifier = Modifier.padding(horizontal = 18.dp),
                        onOpenQueue = onOpenQueue,
                    )
                }
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
            item {
                SectionHeader(
                    modifier = Modifier.padding(horizontal = 18.dp),
                    title = "Recent geüpload",
                    subtitle = "Beperkt bewust tot een uploader/scanner. Voor bewerken, zoeken en administratie ga je door naar de webapp.",
                )
            }
            if (state.documents.isEmpty() && !state.loading && state.error == null) {
                item {
                    EmptyRecentUploads(modifier = Modifier.padding(horizontal = 18.dp))
                }
            } else {
                items(state.documents.take(8), key = { it.id }) { document ->
                    RecentUploadCard(
                        document = document,
                        modifier = Modifier.padding(horizontal = 18.dp),
                        onOpen = { onOpenDocument(document.id) },
                    )
                }
            }
            item { Spacer(modifier = Modifier.height(18.dp)) }
        }
    }
}

@Composable
@OptIn(ExperimentalLayoutApi::class)
private fun UploadMasthead(
    currentUser: UserDto,
    pendingCount: Int,
    totalQueued: Int,
    onRefresh: () -> Unit,
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
                    Image(
                        painter = painterResource(R.drawable.docstore_logo),
                        contentDescription = "Docstore",
                        modifier = Modifier
                            .size(58.dp)
                            .clip(RoundedCornerShape(16.dp)),
                    )
                    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(
                            text = "docstore",
                            color = Color(0xFF83C7FF),
                            style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.ExtraBold,
                        )
                        Text(
                            text = "Mobile uploader",
                            color = Color.White.copy(alpha = 0.82f),
                            style = MaterialTheme.typography.bodyMedium,
                        )
                    }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(2.dp), verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = onRefresh) {
                        Icon(Icons.Rounded.Refresh, contentDescription = "Refresh", tint = Color.White)
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
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text(
                        text = currentUser.tenantName?.takeIf { it.isNotBlank() } ?: "Tenant",
                        color = Color.White,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                    )
                    FlowRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        HeaderBadge(currentUser.name.take(24))
                        HeaderBadge("Queue $pendingCount/$totalQueued")
                        HeaderBadge(if (currentUser.role.equals("superadmin", true)) "Superadmin" else if (currentUser.role.equals("admin", true)) "Admin" else "Gebruiker")
                    }
                }
            }
        }
    }
}

@Composable
private fun HeaderBadge(label: String) {
    Surface(
        shape = RoundedCornerShape(999.dp),
        color = Color.White.copy(alpha = 0.12f),
    ) {
        Text(
            text = label,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
            style = MaterialTheme.typography.labelLarge,
            color = Color.White,
            fontWeight = FontWeight.Bold,
        )
    }
}

@Composable
private fun UploadPrimaryActions(
    modifier: Modifier = Modifier,
    onScanDocument: () -> Unit,
    onImportFile: () -> Unit,
    onOpenQueue: () -> Unit,
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        PrimaryActionButton(
            label = "Scan document",
            icon = Icons.Rounded.PhotoCamera,
            modifier = Modifier.weight(1f),
            colors = listOf(Color(0xFF2F8BFF), Color(0xFF48D3B3)),
            onClick = onScanDocument,
        )
        PrimaryActionButton(
            label = "Bestand kiezen",
            icon = Icons.Rounded.AddPhotoAlternate,
            modifier = Modifier.weight(1f),
            colors = listOf(Color(0xFF315FD4), Color(0xFF51C9B9)),
            onClick = onImportFile,
        )
        OutlinedButton(
            onClick = onOpenQueue,
            modifier = Modifier.weight(0.9f),
            shape = RoundedCornerShape(18.dp),
        ) {
            Icon(Icons.Rounded.CloudUpload, contentDescription = null)
            Spacer(modifier = Modifier.size(8.dp))
            Text("Queue")
        }
    }
}

@Composable
private fun PrimaryActionButton(
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    modifier: Modifier = Modifier,
    colors: List<Color>,
    onClick: () -> Unit,
) {
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(18.dp))
            .clickable(onClick = onClick),
        color = Color.Transparent,
    ) {
        Box(
            modifier = Modifier
                .background(Brush.horizontalGradient(colors))
                .padding(horizontal = 16.dp, vertical = 16.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(icon, contentDescription = null, tint = Color.White)
                Spacer(modifier = Modifier.size(8.dp))
                Text(label, color = Color.White, fontWeight = FontWeight.ExtraBold)
            }
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
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text(
                "DOCUMENT CENTER",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontWeight = FontWeight.ExtraBold,
            )
            Text("Scan -> review -> queue -> upload", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.ExtraBold)
            Text(
                text = "Zoals bij goede scanner-apps blijft de flow smal: document scannen, controleren, lokaal bufferen en pas daarna uploaden. Zo blijft de app betrouwbaar als netwerk of backend even wegvalt.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (totalQueued > 0) {
                Surface(
                    shape = RoundedCornerShape(999.dp),
                    color = MaterialTheme.colorScheme.surfaceVariant,
                ) {
                    Text(
                        text = "$pendingCount wachtend van $totalQueued lokaal opgeslagen item(s)",
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
                        style = MaterialTheme.typography.labelLarge,
                        fontWeight = FontWeight.Bold,
                    )
                }
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
            Text(
                "LOKALE UPLOAD-QUEUE",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontWeight = FontWeight.ExtraBold,
            )
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
private fun SectionHeader(
    modifier: Modifier = Modifier,
    title: String,
    subtitle: String,
) {
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(
            "UPLOADS",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            fontWeight = FontWeight.ExtraBold,
        )
        Text(title, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
        Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun EmptyRecentUploads(modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(22.dp),
        tonalElevation = 2.dp,
        color = MaterialTheme.colorScheme.surface,
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Nog geen recente uploads", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.ExtraBold)
            Text(
                "Nieuwe documenten die via de scanner of file picker zijn geüpload, verschijnen hier als recente items.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
@OptIn(ExperimentalLayoutApi::class)
private fun RecentUploadCard(
    document: DocumentDto,
    modifier: Modifier = Modifier,
    onOpen: () -> Unit,
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(22.dp),
        tonalElevation = 2.dp,
        color = MaterialTheme.colorScheme.surface,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(0.dp)) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(150.dp)
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
                Row(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(10.dp),
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    if (document.ocrProcessed) StatusBadge("OCR")
                    if (document.aiProcessed) StatusBadge("AI")
                }
            }
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text(
                    text = document.subject ?: document.filename,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.ExtraBold,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                FlowRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    document.category?.let { MetaPill(it) }
                    formatDate(document.documentDate)?.let { MetaPill(it) }
                    document.issuer?.takeIf { it.isNotBlank() }?.let { MetaPill(it.take(24)) }
                }
                OutlinedButton(
                    onClick = onOpen,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Icon(Icons.AutoMirrored.Rounded.OpenInNew, contentDescription = null)
                    Spacer(modifier = Modifier.size(8.dp))
                    Text("Open in webapp")
                }
            }
        }
    }
}

@Composable
private fun StatusBadge(label: String) {
    Surface(
        shape = RoundedCornerShape(999.dp),
        color = Color(0xFFE7F7EF),
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
private fun MetaPill(value: String) {
    Surface(
        shape = RoundedCornerShape(999.dp),
        color = Color.Transparent,
    ) {
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(999.dp))
                .background(
                    Brush.horizontalGradient(
                        listOf(Color(0xFFDCEAFF), Color(0xFFDDF8EC)),
                    ),
                )
                .padding(horizontal = 10.dp, vertical = 6.dp),
        ) {
            Text(
                text = value,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurface,
                fontWeight = FontWeight.Bold,
            )
        }
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
