package eu.deknijf.docstoremobile.ui.screens.scan

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.material.icons.rounded.Refresh
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import eu.deknijf.docstoremobile.R
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
            .background(MaterialTheme.colorScheme.background),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            PreviewMasthead(
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
                modifier = Modifier.padding(horizontal = 18.dp),
            )
        }
        itemsIndexed(pages, key = { _, file -> file.absolutePath }) { index, file ->
            PreviewPageCard(
                pageNumber = index + 1,
                totalPages = pages.size,
                file = file,
                modifier = Modifier.padding(horizontal = 18.dp),
            )
        }
        item { Spacer(modifier = Modifier.height(18.dp)) }
    }
}

@Composable
private fun PreviewMasthead(
    currentUser: UserDto,
    pageCount: Int,
    draftCreatedAt: Long,
    onBack: () -> Unit,
    onRescan: () -> Unit,
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
                            androidx.compose.foundation.Image(
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
                        Text("Scan preview", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.ExtraBold, color = Color.White)
                        Text(
                            "${currentUser.tenantName ?: "tenant"} · $pageCount pagina${if (pageCount == 1) "" else "'s"} · ${formatPreviewTimestamp(draftCreatedAt)}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color.White.copy(alpha = 0.82f),
                        )
                    }
                }
                IconButton(onClick = onRescan) {
                    Icon(Icons.Rounded.Refresh, contentDescription = "Opnieuw scannen", tint = Color.White)
                }
            }

            Surface(
                shape = RoundedCornerShape(18.dp),
                color = Color.White.copy(alpha = 0.08f),
            ) {
                Text(
                    text = "Controleer de scan eerst. Pas na bewaren maken we één definitieve PDF en zetten we die in de lokale uploadqueue.",
                    modifier = Modifier.padding(16.dp),
                    color = Color.White,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

@Composable
private fun PreviewInfoCard(
    pageCount: Int,
    onAddPage: () -> Unit,
    onSave: () -> Unit,
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
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                "SCAN REVIEW",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontWeight = FontWeight.ExtraBold,
            )
            Text("Scan controleren", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
            Text(
                "Deze mobile app blijft bewust beperkt tot scannen en uploaden. Je controleert hier de pagina's, voegt indien nodig een extra pagina toe en stuurt daarna één nette PDF door naar de webapp.",
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
    modifier: Modifier = Modifier,
) {
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = MaterialTheme.colorScheme.surface,
        tonalElevation = 2.dp,
        modifier = modifier.fillMaxWidth(),
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
