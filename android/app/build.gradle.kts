plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "net.gununayeti"
    compileSdk = 35
    defaultConfig {
        applicationId = "net.gununayeti"
        minSdk = 26
        targetSdk = 35
        versionCode = (System.getenv("SURUM_KODU") ?: "1").toInt()
        versionName = System.getenv("SURUM_ADI") ?: "1"
    }
    signingConfigs {
        create("yayin") {
            storeFile = file(System.getenv("IMZA_DOSYA") ?: "imza.p12")
            storeType = "pkcs12"
            storePassword = System.getenv("IMZA_SIFRE")
            keyAlias = "gunun"
            keyPassword = System.getenv("IMZA_SIFRE")
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("yayin")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation("androidx.webkit:webkit:1.12.1")
    implementation("androidx.work:work-runtime-ktx:2.9.1")
}
