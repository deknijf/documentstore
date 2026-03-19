# Keep Retrofit/serialization models readable during first MVP phase.
-keep class kotlinx.serialization.** { *; }
-keep class eu.deknijf.docstoremobile.data.model.** { *; }
-dontwarn kotlinx.serialization.**
