# 🎨 Görsel Evrim Raporu: Kart Assetleri ve Sunum Teknolojileri

Bu rapor, mevcut statik heksagonal PNG dosyalarının yerine geçebilecek, projenin siberpunk ve hibrit temasını zirveye taşıyacak 10 farklı görsel yaklaşımı ve teknik uygulama yöntemlerini içermektedir.

---

## 1. Çok Katmanlı Parallaks Sanat (2.5D Deneyimi)
Statik görsellerin katmanlara ayrılarak fare hareketine göre farklı hızlarda kayması.
*   **Yaklaşım:** Mevcut her kart görseli; *Arka Plan (Derinlik)*, *Ana Karakter (Odak)* ve *Efekt/Çerçeve (Ön Plan)* olarak 3-4 katmanlı bir formata dönüştürülür.
*   **Teknik Uygulama:** Pygame içinde `blit` edilirken her katmana bir `depth_factor` (0.05, 0.15, 0.3) atanır. Fare merkeze yaklaştıkça katmanlar çapraz yönlere kayarak derinlik illüzyonu yaratır.
*   **Fayda:** Kartların içindeymiş hissi veren premium bir "canlılık" sağlar.

## 2. ModernGL ile Dinamik Materyal Shader'ları
Kart yüzeylerine GPU üzerinde çalışan özel ışıklandırma ve görsel efektler ekleme.
*   **Yaklaşım:** Pygame'in ModernGL konteyneri üzerinde "Holografik", "Metalik" veya "Sıvı" efektleri veren shader'lar kullanılması.
*   **Teknik Uygulama:** Kartın "Evolved" durumunda, üzerine bir `Fragment Shader` maskesi bindirilir. Bu shader, sanal bir ışık kaynağına göre kartın üzerinde parlamalar (flare) oluşturur.
*   **Fayda:** Evrimleşmiş kartların gerçekten "farklı bir materyalden" yapılmış gibi görünmesini sağlar.

## 3. Vektörel Kart Şasisi (Procedural Chassis)
Görsel ile metinsel verinin birbirinden tamamen ayrıldığı, çözünürlükten bağımsız bir çerçeve sistemi.
*   **Yaklaşım:** Kartın çerçevesi, statları ve isim alanı Pygame'in çizim komutlarıyla (veya SVG'den) dinamik oluşturulur; sadece merkezdeki sanat (art) PNG olarak kalır.
*   **Teknik Uygulama:** `pygame.gfxdraw` veya `shapely` kullanarak anti-aliased heksagonal çerçeveler çizilir. Statlar değiştikçe çerçeve üzerindeki neon çizgiler anlık daralıp genişler.
*   **Fayda:** 4K gibi yüksek çözünürlüklerde pürüzsüz görüntü ve dinamik stat güncellemelerinde temiz görsel sunum.

## 4. Generative AI "Evrim Tabakası" (Bakery System)
Mevcut görsellere AI destekli 2 farklı seviye varyasyonu ekleme.
*   **Yaklaşım:** Her kart için 3 seviyeli bir asset seti hazırlanır: `Base` (Mevcut), `Evolved` (Daha fazla detay ve aura), `Mythic` (Tamamen değişmiş form).
*   **Teknik Uygulama:** Stable Diffusion gibi araçlarla "Evolved" varyasyonları önceden üretilip `v2/assets/cards` altına isimlendirme kuralıyla eklenir.
*   **Fayda:** Oyuncunun evrimleşen her birimi görsel olarak da ödüllendirilmiş hissetmesi.

## 5. 2.5D Perspektif Projeksiyonu (Tilt Mechanics)
Kartların fareye doğru fiziksel olarak eğilmesi.
*   **Yaklaşım:** Hearthstone benzeri, farenin olduğu yöne doğru kartın "yüzünü" dönmesi.
*   **Teknik Uygulama:** `pygame.transform.smoothscale` ve `2x3 dikey deformasyon matrisleri` kullanılarak kartın köşeleri fareye göre daraltılır.
*   **Fayda:** Statik 2D yüzeyi dinamik bir 3D objeye dönüştürür.

## 6. Animasyonlu Spritesheet (Live2D Lite)
Kart içindeki görsellere hafif bir "nefes alma" veya "titreme" hareketi ekleme.
*   **Yaklaşım:** Karakterin saçları, gözleri veya elindeki enerjinin saniyelik bir döngüyle hareket etmesi.
*   **Teknik Uygulama:** Tek bir PNG yerine 4-8 karelik mini spritesheet'ler veya `sin(time)` ile deforme edilen `Skinned Mesh` benzeri basit vertex manipülasyonları.
*   **Fayda:** Oyunun arkada hala canlı ve "yaşıyor" olduğunu hissettirir.

## 7. Derinlik Maskeli "Wiggle" Efekti (Deep Fake 3D)
Tek bir görselden derinlik haritası (Depth Map) çıkararak 3D hissi verme.
*   **Yaklaşım:** Görselin yanında bir de siyah-beyaz derinlik haritası saklanır (Beyaz=Önde, Siyah=Arkada).
*   **Teknik Uygulama:** Shader, derinlik haritasındaki parlaklığa göre pikselleri kaydırır. Mouse hareket ettikçe öndeki pikseller daha çok, arkadakiler daha az kayar.
*   **Fayda:** Katmanlara ayırma zahmetine girmeden tek bir dosya ile tam derinlik hissi.

## 8. 3D Voxel Pre-rendering (Cyber-Isometric)
Heksagonal yapıya uygun, Minecraft-Cyberpunk arası bir stil değişikliği.
*   **Yaklaşım:** Tüm kart görsellerinin 3D voxel modelleri olarak tasarlanıp, 6 farklı açıdan render alınarak sprite olarak gömülmesi.
*   **Teknik Uygulama:** MagicaVoxel gibi araçlarla modeller üretilir, Pygame sadece bunların "izometrik fırlatılmış" sprite'larını kullanır.
*   **Fayda:** Benzersiz, projenin geometrisine (hex) tam uyumlu ve modern bir görsel dil.

## 9. İnteraktif Materyal Shaders (Hologram Mode)
Sadece fareyle üzerine gelindiğinde devreye giren "veri tarama" görünümü.
*   **Yaklaşım:** Hover anında kartın tüm görseli yeşil bir "Hologram" veya "Matrix" akışına dönüşür.
*   **Teknik Uygulama:** Kartın RGB kanalları manipüle edilerek sadece `Green` kanalı tutulur ve üzerine yukarıdan aşağıya kayan neon çizgiler blit edilir.
*   **Fayda:** Teknik/Siberpunk temasını doruk noktasına çıkarır.

## 10. Pre-baked 3D Spritesheets (The Diablo Style)
Gerçek 3D modellerin yüksek kaliteli 2D çıktıları.
*   **Yaklaşım:** Blender'da modellenmiş karakterlerin 60 karelik rotasyon animasyonları alınır.
*   **Teknik Uygulama:** Oyuncu kartı döndürdüğünde veya savaştığında gerçek bir 3D model dönüyormuş gibi hissettiren, önceden render alınmış sprite kareleri kullanılır.
*   **Fayda:** Düşük performanslı bilgisayarlarda bile "AAA 3D Oyun" kalitesinde görsellik sunar.

---

> [!NOTE]
> **Tavsiye:** Başlangıç için **1. Madde (Parallaks)** ve **3. Madde (Vektörel Şasi)** en hızlı ve yüksek etkili (high-impact) sonuçları verecektir. **8. ve 10. Maddeler** ise projenin sanat stilinde köklü bir değişim gerektirir.
