# Göğüs Röntgeni Pnömoni Analizi

## **Takım Üyeleri ve Görev Dağılımı**

- **Kerem:** Modelin eğitimi, veri ön işleme ve hiperparametre ayarları  
- **İrem:** Model sonuçlarının yorumlanması ve klinik raporların oluşturulması  
- **Bertuğ:** Grad-CAM uygulamaları, görsel açıklanabilirlik ve risk değerlendirmeleri  

---

## **Kullanılan Model ve Parametreler**

Bu projede, **MobileNetV2** önceden eğitilmiş modeli kullanılmıştır. Model, TensorFlow ve Keras framework'leri ile oluşturulmuş ve mobil cihazlar için optimize edilmiştir.

### **Model Özellikleri**

- **Önceden Eğitilmiş Ağırlıklar:** `imagenet` veriseti  
- **Base Model:** `MobileNetV2 (include_top=False, weights='imagenet')`  

### **Ekstra Katmanlar**

- **Global Average Pooling:** Daha az parametre ile çıktı oluşturmak için  
- **Dropout:** Ağırlıkların aşırı öğrenmesini engellemek için  
- **Dense Katmanlar:** Sınıflandırma için final katmanları olarak kullanıldı  

### **Hiperparametreler**

- **Batch Size:** 32  
- **Epochs:** 20  
- **Optimizer:** Adam  
- **Loss Function:** Categorical Cross-Entropy  
- **Activation Function:** Softmax (2 sınıf: Pnömoni / Normal)

---

## **Veri Seti**

- **Eğitim Veri Seti:** `train_dir` (Pnömoni ve Normal sınıflarında etiketlenmiş X-ray görüntüleri)  
- **Test Veri Seti:** `test_dir` (Test verisi farklı hastaları içermektedir)

---

## **Veri Artırma Teknikleri**

- `Rescale`: Görsellerin normalize edilmesi (1./255)  
- `Rotation Range`: 15 derece döndürme  
- `Zoom Range`: %10 yakınlaştırma  
- `Horizontal Flip`: Görsellerin yatay çevrilmesi  

---

## **Klinik Rapor Üretim Süreci**

1. **Model Eğitimi:**  
   MobileNetV2 modeli, X-ray verileri üzerinde eğitildi. Eğitim sırasında doğruluk (accuracy) ve kayıp (loss) değerleri dikkate alınarak model optimize edildi.

2. **Model Çıktıları:**  
   Çıktı katmanında softmax fonksiyonu kullanılarak iki sınıf için tahminler yapıldı. Modelin doğruluğu test verisiyle değerlendirildi.

3. **Grad-CAM Açıklanabilirlik:**  
   Grad-CAM (Gradient-weighted Class Activation Mapping) yöntemiyle, modelin karar verdiği bölgeler görsel olarak açıklandı. Sağ alt lobda opasite gibi klinik anlam taşıyan bölgelerde yoğunluk gözlemlendi.

4. **Risk Değerlendirmesi:**  
   Modelin güven skoru ve Grad-CAM haritası birlikte değerlendirilerek hastalık şiddeti belirlendi. Buna göre düşük, orta ve yüksek risk seviyeleri tanımlandı.

5. **Klinik Rapor:**  
   Modelin çıktısına dayanarak, her X-ray için kısa bir tanı cümlesi ve anatomik açıklama içeren klinik raporlar oluşturuldu.

---

## **LLM Karşılaştırması**

Modelin ürettiği klinik raporlar, büyük dil modelleri (LLM’ler) tarafından oluşturulan raporlarla karşılaştırıldı.

### **Kullanılan Metrikler**

- **BLEU:** Kelime düzeyinde n-gram eşleşmesiyle benzerlik ölçümü  
- **ROUGE-L:** Dizisel örtüşmeyi baz alır  
- **BERTScore:** Anlamsal benzerlik ölçümü  

> Bu metriklerin analizine `README.md` dosyasında yorumlarla yer verilmiştir.

LLM’lerin daha doğal dil yapıları kullanmasına rağmen, bazen model çıktılarıyla klinik doğruluk açısından farklılıklar göstermiştir.

---

## **Risk Değerlendirme Mantığı**

| Risk Seviyesi | Güven Skoru        | Grad-CAM Bulguları                    |
|---------------|--------------------|--------------------------------------|
| **Yüksek**    | %75 ve üzeri       | Belirgin opasite bölgeleri mevcut    |
| **Orta**      | %50 - %75 arası    | Daha az belirgin opasite alanları    |
| **Düşük**     | %50'nin altında    | Opasite gözlenmiyor                  |

---
