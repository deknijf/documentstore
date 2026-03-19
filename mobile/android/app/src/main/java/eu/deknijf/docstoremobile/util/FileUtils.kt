package eu.deknijf.docstoremobile.util

import android.content.ContentResolver
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.pdf.PdfDocument
import android.net.Uri
import android.provider.OpenableColumns
import java.io.File
import java.io.FileOutputStream
import java.util.UUID

object FileUtils {
    fun copyUriToAppStorage(
        context: Context,
        uri: Uri,
        fallbackExtension: String = "pdf",
    ): File {
        val resolver = context.contentResolver
        val displayName = queryDisplayName(resolver, uri)
        val extension = displayName.substringAfterLast('.', fallbackExtension).lowercase()
        val targetDir = File(context.filesDir, "pending_uploads").apply { mkdirs() }
        val target = File(targetDir, "${UUID.randomUUID()}.$extension")
        resolver.openInputStream(uri).use { input ->
            requireNotNull(input) { "Kan scanbestand niet openen" }
            target.outputStream().use { output -> input.copyTo(output) }
        }
        return target
    }

    fun queryDisplayName(resolver: ContentResolver, uri: Uri): String {
        resolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
            val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            if (index >= 0 && cursor.moveToFirst()) {
                return cursor.getString(index) ?: "scan.pdf"
            }
        }
        return uri.lastPathSegment ?: "scan.pdf"
    }

    fun copyScanPageToDraftStorage(
        context: Context,
        uri: Uri,
        pageIndex: Int,
    ): File {
        val targetDir = File(context.filesDir, "scan_drafts").apply { mkdirs() }
        val target = File(targetDir, "draft-${UUID.randomUUID()}-${pageIndex + 1}.jpg")
        context.contentResolver.openInputStream(uri).use { input ->
            requireNotNull(input) { "Kan scanpagina niet openen" }
            target.outputStream().use { output -> input.copyTo(output) }
        }
        return target
    }

    fun createPdfFromImages(
        context: Context,
        imageFiles: List<File>,
        outputName: String,
    ): File {
        require(imageFiles.isNotEmpty()) { "Geen scanpagina's beschikbaar" }
        val outputDir = File(context.filesDir, "pending_uploads").apply { mkdirs() }
        val outputFile = File(outputDir, outputName)
        val pdfDocument = PdfDocument()
        imageFiles.forEachIndexed { index, file ->
            val bitmap = BitmapFactory.decodeFile(file.absolutePath)
                ?: error("Kan scanpagina niet lezen: ${file.name}")
            val pageInfo = PdfDocument.PageInfo.Builder(bitmap.width, bitmap.height, index + 1).create()
            val page = pdfDocument.startPage(pageInfo)
            val canvas = page.canvas
            canvas.drawColor(Color.WHITE)
            drawBitmapCentered(canvas, bitmap)
            pdfDocument.finishPage(page)
            bitmap.recycle()
        }
        FileOutputStream(outputFile).use { out ->
            pdfDocument.writeTo(out)
        }
        pdfDocument.close()
        return outputFile
    }

    fun deleteFilesQuietly(files: Iterable<File>) {
        files.forEach { file ->
            runCatching {
                if (file.exists()) {
                    file.delete()
                }
            }
        }
    }

    private fun drawBitmapCentered(canvas: Canvas, bitmap: Bitmap) {
        val paint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)
        canvas.drawBitmap(bitmap, 0f, 0f, paint)
    }
}
