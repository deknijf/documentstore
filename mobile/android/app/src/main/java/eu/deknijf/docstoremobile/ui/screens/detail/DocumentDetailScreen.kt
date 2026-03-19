@file:OptIn(ExperimentalLayoutApi::class)

package eu.deknijf.docstoremobile.ui.screens.detail

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.OpenInNew
import androidx.compose.material.icons.rounded.Description
import androidx.compose.material.icons.rounded.KeyboardArrowDown
import androidx.compose.material.icons.rounded.KeyboardArrowUp
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import eu.deknijf.docstoremobile.data.model.DocumentDto
import eu.deknijf.docstoremobile.data.model.FieldConfidenceDto
import eu.deknijf.docstoremobile.data.model.UserDto
import eu.deknijf.docstoremobile.ui.viewmodel.DocumentDetailViewModel
import java.time.LocalDate
import java.time.temporal.ChronoUnit
import java.time.format.DateTimeFormatter
import java.util.Locale

@Composable
fun DocumentDetailScreen(
    viewModel: DocumentDetailViewModel,
    currentUser: UserDto,
    onBack: () -> Unit,
    onOpenViewer: (String, String) -> Unit,
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    var selectedTab by remember { mutableStateOf("document") }
    var confidenceExpanded by remember { mutableStateOf(false) }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(horizontal = 18.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        item {
            DetailHero(
                currentUser = currentUser,
                loading = state.loading,
                onBack = onBack,
                onRefresh = viewModel::refresh,
            )
        }

        when {
            state.error != null -> {
                item {
                    Surface(
                        color = MaterialTheme.colorScheme.error.copy(alpha = 0.12f),
                        shape = RoundedCornerShape(20.dp),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(
                            text = state.error ?: "Onbekende fout",
                            modifier = Modifier.padding(16.dp),
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodyLarge,
                        )
                    }
                }
            }

            state.document != null -> {
                val doc = state.document!!
                overdueMessage(doc)?.let { warning ->
                    item {
                        Surface(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(20.dp),
                            color = MaterialTheme.colorScheme.error.copy(alpha = 0.12f),
                        ) {
                            Text(
                                text = warning,
                                modifier = Modifier.padding(16.dp),
                                color = MaterialTheme.colorScheme.error,
                                style = MaterialTheme.typography.bodyLarge,
                                fontWeight = FontWeight.SemiBold,
                            )
                        }
                    }
                }

                item {
                    DocumentSummaryCard(
                        document = doc,
                        selectedTab = selectedTab,
                        onSelectTab = { selectedTab = it },
                        onOpenViewer = onOpenViewer,
                    )
                }

                item {
                    MetadataCard(document = doc)
                }

                if (!doc.remark.isNullOrBlank()) {
                    item {
                        RemarkCard(doc.remark)
                    }
                }

                item {
                    ConfidenceHeader(
                        document = doc,
                        expanded = confidenceExpanded,
                        onToggle = { confidenceExpanded = !confidenceExpanded },
                    )
                }

                if (confidenceExpanded && doc.fieldConfidence.isNotEmpty()) {
                    items(doc.fieldConfidence.entries.sortedBy { confidenceLabel(it.key) }, key = { it.key }) { entry ->
                        ConfidenceRow(field = entry.key, confidence = entry.value)
                    }
                }
            }
        }
    }
}

@Composable
private fun DetailHero(
    currentUser: UserDto,
    loading: Boolean,
    onBack: () -> Unit,
    onRefresh: () -> Unit,
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
                Text(
                    text = "Document",
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.ExtraBold,
                )
                Text(
                    text = currentUser.tenantName ?: "Tenant",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
        Box(contentAlignment = Alignment.Center) {
            if (loading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    strokeWidth = 2.dp,
                )
            } else {
                IconButton(onClick = onRefresh) {
                    Icon(Icons.Rounded.Refresh, contentDescription = "Vernieuwen")
                }
            }
        }
    }
}

@Composable
private fun DocumentSummaryCard(
    document: DocumentDto,
    selectedTab: String,
    onSelectTab: (String) -> Unit,
    onOpenViewer: (String, String) -> Unit,
) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(24.dp),
        tonalElevation = 2.dp,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Text(
                text = document.subject ?: document.filename,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.ExtraBold,
            )
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                document.category?.let { SummaryPill(it, listOf(Color(0xFFDCE8FF), Color(0xFFDDF8EC))) }
                if (document.bankPaidVerified || document.paid) {
                    SummaryPill("PAID", listOf(Color(0xFFE6DEFF), Color(0xFFF1E8FF)))
                }
                if (document.aiProcessed) {
                    SummaryPill("AI", listOf(Color(0xFFE1F6EA), Color(0xFFEAFBF2)))
                }
                document.labelNames.take(4).forEach { label ->
                    SummaryPill(label, listOf(Color(0xFFF1F5FF), Color(0xFFF6FAFF)))
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                DetailTabButton(
                    label = "Document",
                    selected = selectedTab == "document",
                    onClick = { onSelectTab("document") },
                )
                DetailTabButton(
                    label = "OCR tekst",
                    selected = selectedTab == "ocr",
                    onClick = { onSelectTab("ocr") },
                )
            }
            if (selectedTab == "document") {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    Button(
                        onClick = { onOpenViewer(document.id, if (document.hasPreprocessed) "viewer" else "original") },
                        shape = RoundedCornerShape(16.dp),
                    ) {
                        Icon(Icons.AutoMirrored.Rounded.OpenInNew, contentDescription = null)
                        Text(" Open")
                    }
                    OutlinedButton(
                        onClick = { onOpenViewer(document.id, "original") },
                        shape = RoundedCornerShape(16.dp),
                    ) {
                        Icon(Icons.Rounded.Description, contentDescription = null)
                        Text(" Origineel")
                    }
                }
                Text(
                    text = if (document.hasPreprocessed) {
                        "Mobiele view gebruikt de geoptimaliseerde documentweergave als die beschikbaar is."
                    } else {
                        "Dit document heeft geen aparte optimized versie. De originele file wordt getoond."
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            } else {
                Surface(
                    shape = RoundedCornerShape(18.dp),
                    color = MaterialTheme.colorScheme.surfaceVariant,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(
                        text = document.ocrText ?: "Geen OCR tekst beschikbaar.",
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(260.dp)
                            .verticalScroll(rememberScrollState())
                            .padding(16.dp),
                        style = MaterialTheme.typography.bodyLarge,
                    )
                }
            }
        }
    }
}

@Composable
private fun DetailTabButton(
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
) {
    val colors = if (selected) {
        listOf(Color(0xFFDCEBFF), Color(0xFFDDF8EC))
    } else {
        listOf(MaterialTheme.colorScheme.surfaceVariant, MaterialTheme.colorScheme.surfaceVariant)
    }
    Surface(
        modifier = Modifier.clip(RoundedCornerShape(16.dp)),
        color = Color.Transparent,
    ) {
        Row(
            modifier = Modifier
                .clip(RoundedCornerShape(16.dp))
                .background(Brush.horizontalGradient(colors))
                .padding(horizontal = 14.dp, vertical = 10.dp)
                .background(Color.Transparent)
                .padding(0.dp),
        ) {
            Text(
                text = label,
                modifier = Modifier.padding(0.dp),
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
    }
}

@Composable
private fun MetadataCard(document: DocumentDto) {
    val rows = buildList {
        add("Afzender" to (document.issuer ?: "-"))
        add("Categorie" to (document.category ?: "-"))
        add("Documentdatum" to formatDate(document.documentDate))
        add("Due date" to formatDate(document.dueDate))
        add("Bedrag" to (document.totalAmount?.let { "${formatMoney(it)} ${document.currency ?: "EUR"}" } ?: "-"))
        add("IBAN" to (document.iban ?: "-"))
        add("Gestructureerde mededeling" to (document.structuredReference ?: "-"))
        add("Betaald" to if (document.paid) "Ja" else "Nee")
        add("Betaald op" to formatDate(document.paidOn))
        add("OCR klaar" to yesNo(document.ocrProcessed))
        add("AI klaar" to yesNo(document.aiProcessed))
        add("Lage confidence velden" to document.lowConfidenceFields.joinToString(", ").ifBlank { "-" })
        add("Laatste update" to formatDateTime(document.updatedAt))
    }

    Surface(
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(24.dp),
        tonalElevation = 2.dp,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                text = "Metadata",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.ExtraBold,
            )
            rows.forEach { (label, value) ->
                DetailRow(label, value)
            }
        }
    }
}

@Composable
private fun RemarkCard(remark: String) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(24.dp),
        tonalElevation = 2.dp,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("Opmerking", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
            Surface(
                shape = RoundedCornerShape(18.dp),
                color = MaterialTheme.colorScheme.surfaceVariant,
            ) {
                Text(
                    text = remark,
                    modifier = Modifier.padding(16.dp),
                    style = MaterialTheme.typography.bodyLarge,
                )
            }
        }
    }
}

@Composable
private fun ConfidenceHeader(
    document: DocumentDto,
    expanded: Boolean,
    onToggle: () -> Unit,
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(24.dp),
        tonalElevation = 2.dp,
        onClick = onToggle,
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column {
                    Text("OCR/AI confidence", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.ExtraBold)
                    Text(
                        text = "${document.fieldConfidence.size} velden · ${document.lowConfidenceFields.size} lage confidence",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                Icon(
                    imageVector = if (expanded) Icons.Rounded.KeyboardArrowUp else Icons.Rounded.KeyboardArrowDown,
                    contentDescription = null,
                )
            }
            if (document.lowConfidenceFields.isNotEmpty()) {
                Surface(
                    color = MaterialTheme.colorScheme.error.copy(alpha = 0.10f),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Text(
                        text = "Lage confidence: ${document.lowConfidenceFields.joinToString(", ")}",
                        modifier = Modifier.padding(14.dp),
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }
        }
    }
}

@Composable
private fun ConfidenceRow(
    field: String,
    confidence: FieldConfidenceDto,
) {
    Surface(
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(20.dp),
        tonalElevation = 1.dp,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(confidenceLabel(field), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    ConfidenceBadge(confidence.score)
                    SourceBadge(confidence.source)
                }
            }
            if (!confidence.reason.isNullOrBlank()) {
                Text(
                    text = confidence.reason,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun ConfidenceBadge(score: Double?) {
    val percentage = ((score ?: 0.0) * 100.0).toInt().coerceIn(0, 100)
    val colors = when {
        percentage >= 90 -> listOf(Color(0xFFDDF8EC), Color(0xFFEAFBF2))
        percentage >= 70 -> listOf(Color(0xFFFDF3CF), Color(0xFFFFF7DC))
        else -> listOf(Color(0xFFFFE3E5), Color(0xFFFFEEF0))
    }
    Surface(
        shape = RoundedCornerShape(999.dp),
        color = Color.Transparent,
    ) {
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(999.dp))
                .background(Brush.horizontalGradient(colors))
                .padding(horizontal = 10.dp, vertical = 6.dp),
        ) {
            Text("$percentage%", fontWeight = FontWeight.ExtraBold, style = MaterialTheme.typography.labelLarge)
        }
    }
}

@Composable
private fun SourceBadge(source: String?) {
    val normalized = source?.uppercase(Locale.getDefault()) ?: "UNKNOWN"
    val colors = when (normalized) {
        "MANUAL" -> listOf(Color(0xFFE6DEFF), Color(0xFFF2E8FF))
        "HINT" -> listOf(Color(0xFFE0EEFF), Color(0xFFF0F7FF))
        else -> listOf(Color(0xFFDDF8EC), Color(0xFFEAFBF2))
    }
    Surface(shape = RoundedCornerShape(999.dp), color = Color.Transparent) {
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(999.dp))
                .background(Brush.horizontalGradient(colors))
                .padding(horizontal = 10.dp, vertical = 6.dp),
        ) {
            Text(normalized, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
private fun SummaryPill(
    label: String,
    colors: List<Color>,
) {
    Surface(shape = RoundedCornerShape(999.dp), color = Color.Transparent) {
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(999.dp))
                .background(Brush.horizontalGradient(colors))
                .padding(horizontal = 12.dp, vertical = 7.dp),
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.Bold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun DetailRow(label: String, value: String) {
    Surface(
        shape = RoundedCornerShape(18.dp),
        color = MaterialTheme.colorScheme.surfaceVariant,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(label, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(value, style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.SemiBold)
        }
    }
}

private fun overdueMessage(document: DocumentDto): String? {
    if (document.paid || document.bankPaidVerified) return null
    val due = parseDate(document.dueDate) ?: return null
    val today = LocalDate.now()
    if (!due.isBefore(today)) return null
    val days = ChronoUnit.DAYS.between(due, today)
    val category = document.category ?: "Document"
    return "$category moest al betaald zijn, deadline was ${formatDate(document.dueDate)} - dit is al $days dagen verstreken"
}

private fun confidenceLabel(field: String): String {
    return when (field) {
        "category" -> "Categorie"
        "issuer" -> "Afzender"
        "subject" -> "Titel / onderwerp"
        "document_date" -> "Documentdatum"
        "due_date" -> "Due date"
        "total_amount" -> "Bedrag"
        "currency" -> "Valuta"
        "iban" -> "IBAN"
        "structured_reference" -> "Gestructureerde mededeling"
        "paid" -> "Betaald"
        "paid_on" -> "Betaald op"
        "summary" -> "Samenvatting"
        else -> field
    }
}

private fun parseDate(raw: String?): LocalDate? {
    val value = raw?.trim().orEmpty()
    if (value.isBlank()) return null
    return runCatching { LocalDate.parse(value.take(10)) }.getOrNull()
}

private fun formatDate(raw: String?): String {
    val value = raw?.trim().orEmpty()
    if (value.isBlank()) return "-"
    return runCatching {
        LocalDate.parse(value.take(10)).format(DateTimeFormatter.ofPattern("dd/MM/yyyy", Locale.getDefault()))
    }.getOrElse { value }
}

private fun formatDateTime(raw: String?): String {
    val value = raw?.trim().orEmpty()
    if (value.isBlank()) return "-"
    return value.replace('T', ' ').take(16)
}

private fun formatMoney(amount: Double): String {
    return String.format(Locale.US, "%.2f", amount).replace('.', ',')
}

private fun yesNo(value: Boolean): String = if (value) "Ja" else "Nee"
