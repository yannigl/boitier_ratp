import wifi, lcd

lcd.init(landscape=True)
lcd.fill(lcd.BLACK)
lcd.text("Connexion...", 20, 140, lcd.GREY, lcd.BLACK, scale=4)

if wifi.connect():
    lcd.fill(lcd.BLACK)
    lcd.text(wifi.ip(), 20, 140, lcd.GREEN, lcd.BLACK, scale=3)
        
else:
    lcd.fill(lcd.BLACK)
    lcd.text("WIFI KO", 20, 140, lcd.RED, lcd.BLACK, scale=6)