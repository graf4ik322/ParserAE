#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Специализированный парсер каталога парфюмерных композиций с сайта aroma-euro.ru
Извлекает названия и бренды парфюмерии и сохраняет в JSON формате
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from urllib.parse import urljoin, urlparse, parse_qs
import re
from typing import List, Dict, Optional
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aroma_euro_parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AromaEuroParser:
    """Специализированный парсер для сайта aroma-euro.ru"""
    
    def __init__(self, base_url: str = "https://aroma-euro.ru"):
        self.base_url = base_url
        self.catalog_url = f"{base_url}/perfume/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': base_url,
        })
        self.perfumes = []
        
    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Получение содержимого страницы"""
        try:
            logger.info(f"Загружаю страницу: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Ошибка при загрузке страницы {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке {url}: {e}")
            return None
    
    def extract_perfume_info(self, product_element) -> Optional[Dict[str, str]]:
        """Извлечение информации о парфюме из элемента товара"""
        try:
            perfume_info = {}
            
            # Поиск названия товара - специфичные селекторы для aroma-euro.ru
            title_element = None
            
            # Попробуем различные селекторы для названия
            title_selectors = [
                '.ty-grid-list__item-name a',
                '.product-title',
                '.ty-product-title',
                'a[class*="product-title"]',
                '.ut2-gl__name a',
                'h3 a',
                'h4 a',
                'a[href*="/perfume/"]'
            ]
            
            for selector in title_selectors:
                title_element = product_element.select_one(selector)
                if title_element:
                    break
            
            # Альтернативный поиск
            if not title_element:
                title_element = product_element.find('a', href=re.compile(r'.*/perfume/.*'))
            
            if title_element:
                title_text = title_element.get_text(strip=True)
                if title_text:
                    perfume_info['full_title'] = title_text
                    
                    # Попытка разделить название и бренд
                    brand, name = self.parse_title(title_text)
                    perfume_info['brand'] = brand
                    perfume_info['name'] = name
                    
                    # Поиск ссылки на товар
                    if title_element.get('href'):
                        perfume_info['url'] = urljoin(self.base_url, title_element['href'])
                else:
                    return None
            else:
                logger.warning("Не найден элемент с названием товара")
                return None
            
            # Поиск цены
            price_selectors = [
                '.ty-price-num',
                '.price',
                '.ty-price',
                '[class*="price"]'
            ]
            
            for selector in price_selectors:
                price_element = product_element.select_one(selector)
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    if price_text and any(char.isdigit() for char in price_text):
                        perfume_info['price'] = price_text
                    break
            
            # Поиск изображения
            img_element = product_element.find('img')
            if img_element and img_element.get('src'):
                perfume_info['image'] = urljoin(self.base_url, img_element['src'])
            
            return perfume_info
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации о товаре: {e}")
            return None
    
    def parse_title(self, title: str) -> tuple:
        """Парсинг названия для разделения на бренд и название"""
        title = title.strip()
        
        # Специфичные паттерны для парфюмерии
        patterns = [
            # Tom Ford - Black Orchid
            r'^([A-Za-z][A-Za-z\s&\.\-\']+?)\s*[-–—]\s*(.+)$',
            # Chanel No 5 (бренд в начале)
            r'^(Chanel|Dior|Gucci|Prada|Versace|Armani|Calvin Klein|Hugo Boss|Dolce Gabbana|Yves Saint Laurent|Tom Ford|Creed|Maison Margiela|Byredo|Le Labo|Diptyque|Hermès|Bottega Veneta|Burberry|Givenchy|Lancome|Estee Lauder|Clinique|Marc Jacobs|Viktor Rolf|Jean Paul Gaultier|Thierry Mugler|Issey Miyake|Kenzo|Cacharel|Davidoff|Montblanc|Bvlgari|Cartier|Chopard|Tiffany|Van Cleef Arpels|Acqua di Parma|Annick Goutal|Penhaligons|Miller Harris|Escentric Molecules|Nasomatto|Amouage|Serge Lutens|Francis Kurkdjian|Frederic Malle|L\'Artisan Parfumeur|Diptyque|Comme des Garcons|Malin Goetz|Fresh|Philosophy|The Body Shop|Lush|Bath Body Works|Victoria\'s Secret|Abercrombie Fitch|Hollister|American Eagle|Aeropostale|Tommy Hilfiger|Ralph Lauren|Polo|Lacoste|Nautica|Perry Ellis|Kenneth Cole|Michael Kors|Coach|Kate Spade|Tory Burch|Donna Karan|DKNY|Vera Wang|Oscar de la Renta|Carolina Herrera|Narciso Rodriguez|Alexander McQueen|Stella McCartney|Vivienne Westwood|John Varvatos|Zegna|Acqua di Gio|Acqua di Gioia|1 Million|Invictus|Sauvage|Bleu de Chanel|Allure|Coco|Chance|Black Opium|Libre|Mon Paris|La Vie Est Belle|Tresor|Miracle|Hypnose|Obsession|Eternity|Escape|CK One|CK Be|Euphoria|Deep Euphoria|Guilty|Flora|Bamboo|Rush|Dylan Blue|Eros|Pour Homme|Femme|Code|Si|Because It\'s You|Stronger With You|The One|Light Blue|Dolce|Imperatrice|Good Girl|Bad Boy|212|Carolina Herrera|Alien|Angel|A Men|Pure Malt|Womanity|Aura|Mugler|L\'Eau d\'Issey|Pleats Please|Nuit d\'Issey|Flower|Jungle|World|Amor Amor|Yes I Am|Anais Anais|Lou Lou|Lolita Lempicka|Cool Water|Hot Water|Silver|Champion|Echo|Zino|White Tea|Silver Mountain Water|Aventus|Green Irish Tweed|Millisime Imperial|Royal Oud|Original Santal|Virgin Island Water|Love in White|Sublime Vanille|Tabarome|Erolfa|Bois du Portugal|Himalaya|Aberdeen Lavender|Royal Princess Oud|Fleurs de Bulgarie|Rose Goldea|Omnia|Serpenti|Man|Aqva|Tygar|Declaration|Terre d\'Hermes|Un Jardin|Voyage|Kelly Caleche|Twilly|H24|Equipage|Amazone|Calyx|Pleasures|White Linen|Beautiful|Youth Dew|Azuree|Private Collection|Sensuous|Bronze Goddess|Intuition|Knowing|Spellbound|Tuscany|White Tea|Daisy|Perfect|Decadence|Honey|Dot|Lola|Flowerbomb|Spicebomb|Good Fortune|Bonbon|Antidote|Only the Brave|Diesel|Fuel for Life|Bad|Loverdose|Sound of the Brave|Spirit|D&G|The One|Pour Femme|Intenso|K|Masculine|Garden|Anthology|Velvet|Rose The One|Royal Night|Devotion|Light Blue Forever|Imperatrice Limited Edition|Sicily|Carnal Flower|Portrait of a Lady|Iris Poudre|Lys Mediterranee|Dans Tes Bras|Une Fleur de Cassie|Bigarade Concentree|Carnal Flower|Dominique Ropion|Noir Epices|Outrageous|Russian Tea|Dries Van Noten|Vetiver Extraordinaire|Bois d\'Argent|Oud Wood|Tobacco Vanille|Neroli Portofino|Lost Cherry|Bitter Peach|Ebene Fume|Oud Minerale|Soleil Blanc|White Suede|Grey Vetiver|Mandarino di Amalfi|Costa Azzurra|Metallique|Ombre Leather|Fucking Fabulous|Tuscan Leather|Champaca Absolute|Plum Japonais|Cafe Rose|Shanghai Lily|Jasmin Rouge|Velvet Orchid|Black Orchid|White Patchouli|Vanille Fatale|Santal Blush|Electric Cherry|Rose Prick|Lavender Extreme|Vert Boheme|Vert d\'Encens|Beau de Jour|Vert de Fleur|Sole di Positano|Fleur de Portofino|Venetian Bergamot|Azure Lime|Acqua Essenziale|Colonia|Colonia Intensa|Colonia Oud|Colonia Pura|Iris Nobile|Peonia Nobile|Rosa Nobile|Magnolia Nobile|Vaniglia del Madagascar|Sandalo|Mirra|Ambra|Oud|Leather|Tobacco|Vetiver|Patchouli|Sandalwood|Cedar|Bergamot|Lemon|Orange|Grapefruit|Mandarin|Lime|Yuzu|Pink Pepper|Black Pepper|Cardamom|Coriander|Ginger|Nutmeg|Cinnamon|Clove|Star Anise|Juniper|Pine|Fir|Eucalyptus|Mint|Basil|Rosemary|Thyme|Lavender|Sage|Geranium|Rose|Jasmine|Tuberose|Ylang Ylang|Neroli|Orange Blossom|Lily|Lily of the Valley|Peony|Iris|Violet|Freesia|Gardenia|Magnolia|Honeysuckle|Mimosa|Osmanthus|Narcissus|Hyacinth|Cyclamen|Peach|Apple|Pear|Plum|Cherry|Strawberry|Raspberry|Blackberry|Blackcurrant|Coconut|Pineapple|Mango|Papaya|Passion Fruit|Fig|Date|Raisin|Prune|Vanilla|Caramel|Honey|Chocolate|Coffee|Cocoa|Almond|Hazelnut|Pistachio|Walnut|Chestnut|Praline|Toffee|Butterscotch|Marshmallow|Cotton Candy|Bubblegum|Candy|Sugar|Cream|Milk|Butter|Cheese|Bread|Cake|Cookie|Pie|Pastry|Doughnut|Waffle|Pancake|Syrup|Jam|Jelly|Marmalade|Compote|Sorbet|Ice Cream|Yogurt|Custard|Pudding|Mousse|Souffle|Meringue|Macaron|Madeleine|Croissant|Baguette|Brioche|Pain au Chocolat|Eclair|Profiterole|Chouquette|Paris Brest|Saint Honore|Opera|Mille Feuille|Tarte Tatin|Clafoutis|Creme Brulee|Flan|Tiramisu|Panna Cotta|Gelato|Granita|Affogato|Cappuccino|Espresso|Latte|Macchiato|Mocha|Hot Chocolate|Tea|Earl Grey|English Breakfast|Green Tea|Oolong|Pu Erh|White Tea|Rooibos|Chamomile|Peppermint|Spearmint|Ginseng|Matcha|Chai|Masala Chai|Turkish Tea|Russian Tea|Moroccan Tea|Indian Tea|Chinese Tea|Japanese Tea|Ceylon Tea|Assam|Darjeeling|Lapsang Souchong|Jasmine Tea|Rose Tea|Chrysanthemum Tea|Hibiscus Tea|Elderflower|Linden|Verbena|Lemon Balm|Fennel|Anise|Licorice|Cardamom Tea|Cinnamon Tea|Ginger Tea|Turmeric Tea|Kombucha|Kefir|Wine|Champagne|Prosecco|Cava|Sake|Beer|Whiskey|Bourbon|Scotch|Rum|Vodka|Gin|Tequila|Brandy|Cognac|Armagnac|Calvados|Grappa|Ouzo|Raki|Absinthe|Pastis|Sambuca|Limoncello|Amaretto|Baileys|Kahlua|Cointreau|Grand Marnier|Chartreuse|Benedictine|Drambuie|Frangelico|Galliano|Jagermeister|Sambuca|Strega|Aperol|Campari|Cynar|Fernet|Punt e Mes|Vermouth|Sherry|Port|Madeira|Marsala|Moscato|Riesling|Gewurztraminer|Pinot Grigio|Pinot Noir|Chardonnay|Sauvignon Blanc|Merlot|Cabernet Sauvignon|Syrah|Shiraz|Grenache|Sangiovese|Chianti|Barolo|Barbaresco|Brunello|Amarone|Prosecco|Franciacorta|Asti|Lambrusco|Soave|Valpolicella|Montepulciano|Nero d\'Avola|Primitivo|Aglianico|Fiano|Falanghina|Greco|Vermentino|Pecorino|Passerina|Trebbiano|Malvasia|Moscato d\'Asti|Brachetto|Dolcetto|Barbera|Nebbiolo|Cortese|Arneis|Roero|Gavi|Orvieto|Frascati|Est Est Est|Cesanese|Montepulciano d\'Abruzzo|Sangiovese di Romagna|Lambrusco di Sorbara|Lambrusco Grasparossa|Lambrusco Salamino|Pignoletto|Albana|Trebbiano d\'Abruzzo|Pecorino d\'Abruzzo|Montepulciano del Molise|Taurasi|Greco di Tufo|Fiano di Avellino|Lacryma Christi|Falanghina del Sannio|Aglianico del Taburno|Piedirosso|Sciascinoso|Coda di Volpe|Biancolella|Forastera|San Lunardo|Caprettone|Ginestra|Olivella|Ripolo|Uva Rara|Vespolina|Bonarda|Croatina|Ruchè|Grignolino|Freisa|Brachetto d\'Acqui|Moscato Rosa|Gewürztraminer|Sylvaner|Müller Thurgau|Pinot Bianco|Pinot Nero|Schiava|Lagrein|Teroldego|Marzemino|Nosiola|Chardonnay|Sauvignon|Merlot|Cabernet|Refosco|Friulano|Ribolla Gialla|Malvasia Istriana|Vitovska|Glera|Prosecco di Valdobbiadene|Prosecco di Conegliano|Cartizze|Rive|Millesimato|Brut|Extra Brut|Pas Dosé|Extra Dry|Dry|Demi Sec|Dolce|Spumante|Frizzante|Tranquillo|Novello|Riserva|Superiore|Classico|DOCG|DOC|IGT|Vino da Tavola|Biologico|Biodinamico|Naturale|Orange Wine|Pet Nat|Ancestrale|Col Fondo|Rifermentato|Charmat|Martinotti|Champenoise|Metodo Classico|Cuvée|Assemblage|Blend|Monovitigno|Cru|Vigna|Vigneto|Terroir|Millésime|Annata|Vendemmia|Harvest|Grape|Uva|Vine|Vite|Vineyard|Vignoble|Winery|Cantina|Cave|Cellar|Barrel|Botte|Tonneau|Barrique|Oak|Rovere|French Oak|American Oak|Slavonian Oak|Acacia|Cherry|Ciliegio|Chestnut|Castagno|Steel|Acciaio|Concrete|Cemento|Amphora|Anfora|Qvevri|Tinaja|Foudre|Puncheon|Hogshead|Firkin|Pin|Tun|Vat|Tank|Serbatoio|Fermentation|Fermentazione|Maceration|Macerazione|Malolactic|Malolattica|Lees|Fecce|Batonnage|Riddling|Remuage|Disgorgement|Sboccatura|Dosage|Liqueur|Expedition|Tirage|Prise de Mousse|Autolysis|Autolisi|Aging|Invecchiamento|Maturation|Maturazione|Evolution|Evoluzione|Peak|Picco|Decline|Declino|Drinking Window|Finestra di Bevibilità|Cellar|Cantina|Storage|Conservazione|Temperature|Temperatura|Humidity|Umidità|Light|Luce|Vibration|Vibrazione|Cork|Sughero|Screwcap|Tappo a Vite|Synthetic|Sintetico|Glass|Vetro|Bottle|Bottiglia|Magnum|Double Magnum|Jeroboam|Rehoboam|Methuselah|Salmanazar|Balthazar|Nebuchadnezzar|Melchior|Solomon|Sovereign|Primat|Melchizedek)\s+(.+)$',
            # Brand Name (in parentheses)
            r'^(.+?)\s*\(([^)]+)\).*$',
            # Brand space Name
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(.+)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, title, re.IGNORECASE)
            if match:
                brand = match.group(1).strip()
                name = match.group(2).strip()
                
                # Проверяем, что бренд разумной длины
                if len(brand.split()) <= 4 and len(brand) <= 50:
                    return brand, name
        
        # Если не удалось разделить, пытаемся найти известные бренды в начале
        known_brands = [
            'Tom Ford', 'Chanel', 'Dior', 'Gucci', 'Prada', 'Versace', 'Armani', 
            'Calvin Klein', 'Hugo Boss', 'Dolce Gabbana', 'Yves Saint Laurent',
            'Creed', 'Maison Margiela', 'Byredo', 'Le Labo', 'Diptyque', 'Hermès',
            'Bottega Veneta', 'Burberry', 'Givenchy', 'Lancome', 'Estee Lauder'
        ]
        
        title_lower = title.lower()
        for brand in known_brands:
            if title_lower.startswith(brand.lower()):
                remaining = title[len(brand):].strip()
                if remaining.startswith('-') or remaining.startswith('–') or remaining.startswith('—'):
                    remaining = remaining[1:].strip()
                return brand, remaining if remaining else title
        
        # Если ничего не найдено, возвращаем пустой бренд и полное название
        return "", title
    
    def get_all_pages_urls(self) -> List[str]:
        """Получение ссылок на все страницы каталога"""
        urls = [self.catalog_url]
        
        soup = self.get_page_content(self.catalog_url)
        if not soup:
            return urls
        
        # Поиск пагинации для aroma-euro.ru
        pagination_selectors = [
            '.ty-pagination__item a',
            '.pagination a',
            'a[href*="page-"]',
            '.ty-pagination a'
        ]
        
        for selector in pagination_selectors:
            page_links = soup.select(selector)
            if page_links:
                for link in page_links:
                    href = link.get('href')
                    if href and ('page-' in href or 'page=' in href):
                        full_url = urljoin(self.base_url, href)
                        if full_url not in urls:
                            urls.append(full_url)
                break
        
        logger.info(f"Найдено страниц для парсинга: {len(urls)}")
        return sorted(urls)
    
    def parse_catalog_page(self, url: str) -> List[Dict[str, str]]:
        """Парсинг одной страницы каталога"""
        soup = self.get_page_content(url)
        if not soup:
            return []
        
        perfumes = []
        
        # Специфичные селекторы для aroma-euro.ru
        product_selectors = [
            '.ty-grid-list__item',
            '.ut2-gl__item',
            '.ty-column4',
            '.product-item',
            'div[class*="grid"]',
            'div[class*="product"]',
            'div[class*="item"]'
        ]
        
        products = []
        for selector in product_selectors:
            found_products = soup.select(selector)
            if found_products:
                products = found_products
                logger.info(f"Найдено товаров с селектором '{selector}': {len(products)}")
                break
        
        # Если основные селекторы не сработали, попробуем найти товары по ссылкам
        if not products:
            # Ищем все ссылки на товары парфюмерии
            product_links = soup.find_all('a', href=re.compile(r'.*/perfume/[^/]+/?$'))
            if product_links:
                # Группируем по родительским элементам
                parents = set()
                for link in product_links:
                    parent = link.find_parent(['div', 'li', 'article'])
                    if parent:
                        parents.add(parent)
                products = list(parents)
                logger.info(f"Найдено товаров по ссылкам: {len(products)}")
        
        if not products:
            logger.warning(f"Не найдено товаров на странице: {url}")
            # Попробуем сохранить HTML для анализа
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            logger.info("HTML страницы сохранен в debug_page.html для анализа")
        
        for product in products:
            perfume_info = self.extract_perfume_info(product)
            if perfume_info:
                perfumes.append(perfume_info)
        
        logger.info(f"Извлечено парфюмов со страницы {url}: {len(perfumes)}")
        return perfumes
    
    def parse_all_catalog(self) -> List[Dict[str, str]]:
        """Парсинг всего каталога"""
        logger.info("Начинаю парсинг каталога парфюмерии aroma-euro.ru")
        
        # Получаем все страницы каталога
        page_urls = self.get_all_pages_urls()
        
        all_perfumes = []
        
        for i, url in enumerate(page_urls, 1):
            logger.info(f"Обрабатываю страницу {i}/{len(page_urls)}: {url}")
            
            page_perfumes = self.parse_catalog_page(url)
            all_perfumes.extend(page_perfumes)
            
            # Задержка между запросами
            if i < len(page_urls):
                time.sleep(3)  # Увеличиваем задержку для надежности
        
        # Удаление дубликатов
        unique_perfumes = []
        seen_titles = set()
        seen_urls = set()
        
        for perfume in all_perfumes:
            title = perfume.get('full_title', '')
            url = perfume.get('url', '')
            
            # Используем URL как основной критерий уникальности
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_perfumes.append(perfume)
            elif not url and title and title not in seen_titles:
                seen_titles.add(title)
                unique_perfumes.append(perfume)
        
        logger.info(f"Всего найдено уникальных парфюмов: {len(unique_perfumes)}")
        self.perfumes = unique_perfumes
        return unique_perfumes
    
    def save_to_json(self, filename: str = 'aroma_euro_perfumes.json') -> None:
        """Сохранение данных в JSON файл"""
        try:
            # Подготавливаем данные для сохранения
            save_data = {
                'metadata': {
                    'source': 'aroma-euro.ru',
                    'parsing_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_count': len(self.perfumes),
                    'parser_version': 'final-2.0'
                },
                'perfumes': self.perfumes
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Данные сохранены в файл: {filename}")
            logger.info(f"Количество записей: {len(self.perfumes)}")
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении в JSON: {e}")
    
    def get_statistics(self) -> Dict[str, int]:
        """Получение статистики по парсингу"""
        if not self.perfumes:
            return {}
        
        brands = set()
        names_with_brands = 0
        names_without_brands = 0
        with_urls = 0
        with_prices = 0
        with_images = 0
        
        for perfume in self.perfumes:
            brand = perfume.get('brand', '').strip()
            if brand:
                brands.add(brand)
                names_with_brands += 1
            else:
                names_without_brands += 1
            
            if perfume.get('url'):
                with_urls += 1
            if perfume.get('price'):
                with_prices += 1
            if perfume.get('image'):
                with_images += 1
        
        return {
            'total_perfumes': len(self.perfumes),
            'unique_brands': len(brands),
            'names_with_brands': names_with_brands,
            'names_without_brands': names_without_brands,
            'with_urls': with_urls,
            'with_prices': with_prices,
            'with_images': with_images
        }


def main():
    """Основная функция"""
    parser = AromaEuroParser()
    
    try:
        # Парсинг каталога
        perfumes = parser.parse_all_catalog()
        
        if perfumes:
            # Сохранение в JSON
            parser.save_to_json('aroma_euro_perfumes.json')
            
            # Вывод статистики
            stats = parser.get_statistics()
            print("\n" + "="*50)
            print("СТАТИСТИКА ПАРСИНГА AROMA-EURO.RU")
            print("="*50)
            print(f"Всего парфюмов: {stats.get('total_perfumes', 0)}")
            print(f"Уникальных брендов: {stats.get('unique_brands', 0)}")
            print(f"С определенным брендом: {stats.get('names_with_brands', 0)}")
            print(f"Без бренда: {stats.get('names_without_brands', 0)}")
            print(f"С URL: {stats.get('with_urls', 0)}")
            print(f"С ценами: {stats.get('with_prices', 0)}")
            print(f"С изображениями: {stats.get('with_images', 0)}")
            
            # Показать первые несколько записей
            print("\n" + "="*50)
            print("ПРИМЕРЫ ЗАПИСЕЙ")
            print("="*50)
            for i, perfume in enumerate(perfumes[:10], 1):
                print(f"\n{i}. {perfume.get('full_title', 'Без названия')}")
                if perfume.get('brand'):
                    print(f"   Бренд: {perfume['brand']}")
                if perfume.get('name'):
                    print(f"   Название: {perfume['name']}")
                if perfume.get('price'):
                    print(f"   Цена: {perfume['price']}")
                if perfume.get('url'):
                    print(f"   URL: {perfume['url']}")
            
            # Топ брендов
            brand_counts = {}
            for perfume in perfumes:
                brand = perfume.get('brand', '').strip()
                if brand:
                    brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            if brand_counts:
                print("\n" + "="*50)
                print("ТОП-10 БРЕНДОВ")
                print("="*50)
                sorted_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)
                for i, (brand, count) in enumerate(sorted_brands[:10], 1):
                    print(f"{i:2d}. {brand}: {count} товаров")
        else:
            logger.warning("Не удалось извлечь данные о парфюмах")
            print("\nПарсинг не дал результатов. Проверьте логи для диагностики.")
            
    except KeyboardInterrupt:
        logger.info("Парсинг прерван пользователем")
        print("\nПарсинг прерван пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        print(f"\nКритическая ошибка: {e}")
        raise


if __name__ == "__main__":
    main()