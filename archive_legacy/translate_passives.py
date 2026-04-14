import re

# Çeviri sözlüğü (Türkçe → İngilizce, kısaltılmış)
translations = {
    "Boardda olduğu sürece komşu Mitoloji kartlarına +1 Anlam yayılır.": "While on board, spreads +1 Meaning to neighboring Mythology cards.",
    "Boardda 3+ Mitoloji kartı varken tüm Mitoloji kartlarına +1 Prestij.": "When 3+ Mythology cards on board, +1 Prestige to all Mythology cards.",
    "Bu karta combat başlatan rakip kart o tur -1 Hız alan etkisi alır.": "Opponent cards initiating combat against this card take -1 Speed field effect that turn.",
    "Boardda olduğu sürece komşu rakip kartların Bağlantı kenarları -1 alan etkisi alır.": "While on board, neighboring enemy cards' Connection edges take -1 field effect.",
    "Boardda 2+ Sanat kartı varken tüm Sanat kartlarına +1 Prestij.": "When 2+ Art cards on board, +1 Prestige to all Art cards.",
    "Boardda 2+ Sanat kartı varken Prestij kenarlarına +1.": "When 2+ Art cards on board, +1 to Prestige edges.",
    "Eclipse aktifken komşu dost kartlara +1 Sır yayar.": "When Eclipse active, spreads +1 Secret to neighboring ally cards.",
    "Boardda 3+ Doğa kartı varken tüm dost kartlara +1 Uyum.": "When 3+ Nature cards on board, +1 Harmony to all ally cards.",
    "Komşu dost Doğa kartlarına her tur +1 Uyum yayar.": "Spreads +1 Harmony to neighboring ally Nature cards per turn.",
    "Boardda 4+ Doğa kartı varken tüm Doğa kartlarına +1 Yayılım.": "When 4+ Nature cards on board, +1 Spread to all Nature cards.",
    "Boardda olduğu sürece rakibin komşu kartları her tur -1 İz alır.": "While on board, opponent's neighboring cards take -1 Trace per turn.",
    "Boardda 3+ Kozmos kartı varken tüm Kozmos kartlarına +1 Çekim.": "When 3+ Cosmos cards on board, +1 Gravity to all Cosmos cards.",
    "Boardda 4+ Kozmos kartı varken Çekim kenarları +2 olur.": "When 4+ Cosmos cards on board, Gravity edges +2.",
    "Komşu dost Kozmos kartlarına +1 Uyum yayar.": "Spreads +1 Harmony to neighboring ally Cosmos cards.",
    "Boardda olduğu sürece rakibin merkez kartına her tur -1 Çekim çeker.": "While on board, pulls -1 Gravity from opponent's center card per turn.",
    "Boardda 3+ Kozmos kartı varken tüm kartlara +1 Yayılım.": "When 3+ Cosmos cards on board, +1 Spread to all cards.",
    "Komşu tüm kartları (dost/rakip) her tur -1 Hız alan etkisi alır.": "Neighboring all cards (ally/enemy) take -1 Speed field effect per turn.",
    "Boardda 3+ Bilim kartı varken tüm Bilim kartlarına +1 Zeka.": "When 3+ Science cards on board, +1 Intelligence to all Science cards.",
    "Komşu dost Bilim kartlarına +1 Zeka yayar, elektrik zinciri.": "Spreads +1 Intelligence to neighboring ally Science cards, electric chain.",
    "Boardda olduğu sürece tüm kartların en yüksek kenarı her 3 turda -1 azalır.": "While on board, all cards' highest edge decreases by -1 every 3 turns.",
    "Boardda 4+ Bilim kartı varken tüm Bilim kartlarına +1 Zeka +1 Anlam.": "When 4+ Science cards on board, +1 Intelligence +1 Meaning to all Science cards.",
    "Boardda olduğu sürece tüm kartların Çekim kenarları +1 olur.": "While on board, all cards' Gravity edges +1.",
    "Boardda 3+ Tarih kartı varken rakibin en yüksek statına -1 alan etkisi.": "When 3+ History cards on board, -1 field effect to opponent's highest stat.",
    "Boardda 3+ farklı kategoriden kart varken tüm kartlara +1 Anlam.": "When 3+ cards from different categories on board, +1 Meaning to all cards.",
    "Boardda 4+ Tarih kartı varken tüm dost kartlara +1 Dayanıklılık.": "When 4+ History cards on board, +1 Durability to all ally cards.",
    "Boardda olduğu sürece tüm rakip kartların Yayılım kenarları her tur -1 alır.": "While on board, all enemy cards' Spread edges take -1 per turn.",
    "Zihin grubu eşleşmelerinde combo +1 ekstra puan üretir.": "Produces +1 extra combo point in Mind group matches.",
    "Bağlantı grubu eşleşmelerinde +1 ekstra combat bonusu.": "In Connection group matches, +1 extra combat bonus.",
    "Aynı turda 2+ combo eşleşmesi olursa +1 ekstra puan.": "If 2+ combo matches in same turn, +1 extra point.",
    "Combo eşleşmesi gerçekleştiğinde +1 altın kazanılır (maks 2/tur).": "When combo match occurs, gain +1 gold (max 2/turn).",
    "Combo eşleşmesi olduğunda komşu dost kartlara +1 Uyum o tur.": "When combo match occurs, +1 Harmony to neighboring ally cards that turn.",
    "Kozmos kartlarıyla combo kurulduğunda +2 ekstra puan.": "When combo formed with Cosmos cards, +2 extra points.",
    "ZİHİN grubu combo eşleşmelerinde +2 ekstra puan üretir.": "Produces +2 extra points in MIND group combo matches.",
    "Board'da altın oran yerleşimi (merkez + 6 komşu dolu) varsa +3 puan.": "If golden ratio placement (center + 6 neighbors full) on board, +3 points.",
    "Boarddaki komşu dost kartların kopya sayacı her tur +1 ekstra ilerler.": "Neighboring ally cards' copy counters advance +1 extra per turn.",
    "Kopya güçlenme gerçekleştiğinde komşu dost karta da aynı güçlenme uygulanır.": "When copy strengthening occurs, apply same strengthening to neighboring ally card.",
    "Her kopya güçlenmede +1 yerine +2 bonus alır.": "In each copy strengthening, gains +2 instead of +1.",
    "Kopya sayacı her tur +1 ekstra ilerler (Catalyst etkisini kopyalar).": "Copy counter advances +1 extra per turn (copies Catalyst effect).",
    "Kopya güçlenme anında tüm boarddaki dost kartlar o tur +1 tüm kenarlara.": "At copy strengthening, all ally cards on board +1 to all edges that turn.",
    "Kopya güçlenme gerçekleştiğinde +2 altın kazanılır.": "When copy strengthening occurs, gain +2 gold.",
    "Her kopya güçlenmede bir sonraki eşik 1 tur erken gelir.": "In each copy strengthening, next threshold comes 1 turn early.",
    "Kopya güçlenme anında +1 Dayanıklılık tüm kopyalara kalıcı eklenir.": "At copy strengthening, +1 Durability permanently to all copies.",
    "Bu kart yok edilirse bir sonraki tur +3 altın kazanılır (1 kez).": "If this card is destroyed, gain +3 gold next turn (once).",
    "Yok edildiğinde tüm kenarlar 1'e sıfırlanarak boardda kalır (1 kez).": "When destroyed, all edges reset to 1 and stay on board (once).",
    "Combat kaybedip kenar kaybettiğinde o kenar 1 sonraki tur +1 geri kazanır.": "When losing combat and an edge, regain +1 to that edge next turn.",
    "Yok edilmeden önce komşu dost kartlara +1 Dayanıklılık verir.": "Before destruction, grants +1 Durability to neighboring ally cards.",
    "Yok edilen ilk kez boardda kalır, tüm kenarlar 2'ye sıfırlanır (1 kez).": "First time destroyed, stays on board with all edges reset to 2 (once).",
    "Yok edilmek üzereyken Dayanıklılık grubu kenarları 3'e sıfırlanır, boardda kalır (2 kez).": "When about to be destroyed, reset Durability group edges to 3, stay on board (twice).",
    "Yok edilmeden önce tüm komşu dost kartlara +2 Dayanıklılık verir.": "Before destruction, grants +2 Durability to all neighboring ally cards.",
    "Yok edilmek üzereyken patlama: komşu tüm kartlara (dost/rakip) -1 en yüksek kenar.": "When about to be destroyed, explosion: -1 to highest edge of all neighboring cards (ally/enemy).",
    "Yok edildiğinde komşu 3 rakip karta -2 en yüksek kenar hasarı verir.": "When destroyed, deals -2 to highest edge of 3 neighboring enemy cards.",
    "Her tur market'te ◆◆◆◆ veya ◆◆◆◆◆ kart varsa +1 altın.": "If ◆◆◆◆ or ◆◆◆◆◆ cards in market per turn, +1 gold.",
    "Her tur market yenilendiğinde +1 altın kazanılır.": "Gain +1 gold whenever market refreshes per turn.",
    "Her tur +1 ekstra altın geliri (sabit bonus).": "Gain +1 extra gold income per turn (fixed bonus).",
    "Market'te yeni kart türü ilk görüldüğünde +2 altın.": "When new card type first seen in market, +2 gold.",
    "Her tur 2+ kart satın alınırsa +1 ekstra altın.": "If 2+ cards bought per turn, +1 extra gold.",
    "Her tur market yenilemesi 1 altın indirimli.": "Market refresh 1 gold discounted per turn.",
    "Faiz geliri +1 ekstra (normal faiz hesabına eklenir).": "Interest income +1 extra (added to normal interest calculation).",
    "Market'ten kart alındığında %25 ihtimalle 1 altın iade.": "When buying card from market, 25% chance to refund 1 gold.",
    "Oyun boyunca ilk ◆◆◆◆◆ kart alındığında +5 altın bonus.": "First ◆◆◆◆◆ card bought throughout game grants +5 gold bonus.",
}

# Dosya oku ve çevir
file_path = "assets/data/passives.txt"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Her çeviriyi uygula
for tr, en in translations.items():
    content = content.replace(tr, en)

# Kaydet
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("passives.txt çevirisi tamamlandı!")
