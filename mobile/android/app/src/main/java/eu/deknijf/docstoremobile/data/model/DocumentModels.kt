package eu.deknijf.docstoremobile.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class FieldConfidenceDto(
    val score: Double? = null,
    val reason: String? = null,
    val source: String? = null,
)

@Serializable
data class DocumentDto(
    val id: String,
    val filename: String,
    @SerialName("content_type") val contentType: String,
    @SerialName("has_preprocessed") val hasPreprocessed: Boolean = false,
    @SerialName("thumbnail_path") val thumbnailPath: String? = null,
    val status: String,
    val category: String? = null,
    val issuer: String? = null,
    val subject: String? = null,
    @SerialName("document_date") val documentDate: String? = null,
    @SerialName("due_date") val dueDate: String? = null,
    @SerialName("total_amount") val totalAmount: Double? = null,
    val currency: String? = null,
    val iban: String? = null,
    @SerialName("structured_reference") val structuredReference: String? = null,
    val paid: Boolean = false,
    @SerialName("paid_on") val paidOn: String? = null,
    @SerialName("bank_paid_verified") val bankPaidVerified: Boolean = false,
    val remark: String? = null,
    @SerialName("ocr_text") val ocrText: String? = null,
    @SerialName("ocr_processed") val ocrProcessed: Boolean = false,
    @SerialName("ai_processed") val aiProcessed: Boolean = false,
    @SerialName("label_names") val labelNames: List<String> = emptyList(),
    @SerialName("field_confidence") val fieldConfidence: Map<String, FieldConfidenceDto> = emptyMap(),
    @SerialName("low_confidence_fields") val lowConfidenceFields: List<String> = emptyList(),
    @SerialName("created_at") val createdAt: String,
    @SerialName("updated_at") val updatedAt: String,
)
