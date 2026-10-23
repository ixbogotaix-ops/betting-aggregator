/**
 * Модуль перевода спортивных названий (команд, турниров, лиг) на русский язык.
 * Содержит полную базу топ-клубов Европы, Южной Америки, КХЛ, НХЛ, НБА,
 * а также алгоритм фонетической транслитерации для неизвестных клубов.
 */

// База официальных русских названий клубов
export const TEAMS_RU_MAP = {
  // --- Баскетбол / Евролига / Французские клубы ---
  "asvel": "АСВЕЛ Лион",
  "asvel lyon": "АСВЕЛ Лион",
  "asvel lyon-villeurbanne": "АСВЕЛ Лион",
  "asvel lyon villeurbanne": "АСВЕЛ Лион",
  "ldlc asvel": "АСВЕЛ Лион",
  "ldlc asvel villeurbanne": "АСВЕЛ Лион",

  // --- Нидерланды / Бельгия / Болгария ---
  "nec nijmegen": "Неймеген",
  "nijmegen": "Неймеген",
  "nec": "Неймеген",
  "levski sofia": "Левски София",
  "pfc levski sofia": "Левски София",
  "levski": "Левски София",

  // --- Лига Европы / Лига Чемпионов / Топ Европы ---
  "ferencvaros tc": "Ференцварош",
  "ferencvaros": "Ференцварош",
  "ferencvarosi tc": "Ференцварош",
  "viktoria plzen": "Виктория Пльзень",
  "viktoria plzeň": "Виктория Пльзень",
  "plzen": "Виктория Пльзень",
  "plzeň": "Виктория Пльзень",
  "red bull salzburg": "Ред Булл Зальцбург",
  "rb salzburg": "Ред Булл Зальцбург",
  "salzburg": "Зальцбург",
  "ac milan": "Милан",
  "milan": "Милан",
  "celta vigo": "Сельта",
  "celta": "Сельта",
  "juventus": "Ювентус",
  "sk sturm graz": "Штурм Грац",
  "sturm graz": "Штурм Грац",
  "sturm": "Штурм Грац",
  "bournemouth": "Борнмут",
  "afc bournemouth": "Борнмут",
  "dinamo zagreb": "Динамо Загреб",
  "gnk dinamo zagreb": "Динамо Загреб",
  "anderlecht": "Андерлехт",
  "rsc anderlecht": "Андерлехт",
  "benfica": "Бенфика",
  "sl benfica": "Бенфика",
  "celtic": "Селтик",
  "celtic fc": "Селтик",
  "marseille": "Марсель",
  "olympique marseille": "Марсель",
  "olympiakos": "Олимпиакос",
  "olympiakos piraeus": "Олимпиакос",
  "olympiacos": "Олимпиакос",
  "1899 hoffenheim": "Хоффенхайм",
  "tsg 1899 hoffenheim": "Хоффенхайм",
  "hoffenheim": "Хоффенхайм",
  "besiktas": "Бешикташ",
  "besiktas jk": "Бешикташ",
  "beşiktaş": "Бешикташ",
  "beşiktaş j.k.": "Бешикташ",
  "bayern munchen": "Бавария",
  "fc bayern munchen": "Бавария",
  "bayern munich": "Бавария",
  "fc bayern münchen": "Бавария",
  "az alkmaar": "АЗ Алкмар",
  "az": "АЗ Алкмар",
  "hapoel beer sheva": "Хапоэль Беэр-Шева",
  "hapoel be'er sheva": "Хапоэль Беэр-Шева",
  "lyon": "Лион",
  "olympique lyonnais": "Лион",
  "crystal palace": "Кристал Пэлас",
  "sparta praha": "Спарта Прага",
  "sparta prague": "Спарта Прага",
  "lillestrom": "Лиллестрём",
  "lillestrøm": "Лиллестрём",
  "brighton": "Брайтон",
  "brighton & hove albion": "Брайтон",
  "brighton and hove albion": "Брайтон",
  "kauno zalgiris": "Кауно Жальгирис",
  "kauno žalgiris": "Кауно Жальгирис",
  "sc freiburg": "Фрайбург",
  "freiburg": "Фрайбург",
  "fk jablonec": "Яблонец",
  "jablonec": "Яблонец",
  "atalanta": "Аталанта",
  "atalanta bc": "Аталанта",
  "pafos": "Пафос",
  "fc pafos": "Пафос",
  "st. truiden": "Сент-Трюйден",
  "sint-truidense": "Сент-Трюйден",
  "st truiden": "Сент-Трюйден",
  "fc iberia 1999": "Иберия 1999",
  "iberia 1999": "Иберия 1999",
  "twente": "Твенте",
  "fc twente": "Твенте",
  "fc thun": "Тун",
  "thun": "Тун",
  "rennes": "Ренн",
  "stade rennais": "Ренн",
  "ofi": "ОФИ",
  "ofi crete": "ОФИ",
  "gent": "Гент",
  "kaa gent": "Гент",
  "aarhus": "Орхус",
  "agf aarhus": "Орхус",
  "ajax": "Аякс",
  "afc ajax": "Аякс",
  "hnk hajduk split": "Хайдук Сплит",
  "hajduk split": "Хайдук Сплит",
  "kups": "КуПС",
  "kuopion palloseura": "КуПС",
  "trabzonspor": "Трабзонспор",
  "fc lugano": "Лугано",
  "lugano": "Лугано",
  "fk crvena zvezda": "Црвена Звезда",
  "crvena zvezda": "Црвена Звезда",
  "red star belgrade": "Црвена Звезда",
  "panathinaikos": "Панатинаикос",
  "torreense": "Торренсе",
  "sunderland": "Сандерленд",
  "cska sofia": "ЦСКА София",
  "monaco": "Монако",
  "as monaco": "Монако",
  "egnatia rrogozhine": "Эгнатия",
  "egnatia rrogozhinë": "Эгнатия",
  "fc midtjylland": "Мидтьюлланд",
  "midtjylland": "Мидтьюлланд",
  "mjallby aif": "Мьельбю",
  "inter club d'escaldes": "Интер Эскальдес",
  "borac banja luka": "Борац Баня-Лука",
  "riga": "Рига",
  "fc riga": "Рига",
  "kairat almaty": "Кайрат",
  "kairat": "Кайрат",
  "universitatea craiova": "Университатя Крайова",
  "craiova": "Крайова",
  "getafe": "Хетафе",
  "celje": "Целе",
  "nk celje": "Целе",
  "omonia nicosia": "Омония",
  "omonia": "Омония",
  "lech poznan": "Лех Познань",
  "bayer leverkusen": "Байер Леверкузен",
  "leverkusen": "Байер Леверкузен",
  "union st. gilloise": "Юнион Сент-Жиллуаз",
  "union saint-gilloise": "Юнион Сент-Жиллуаз",
  "real sociedad": "Реал Сосьедад",
  "fc copenhagen": "Копенгаген",
  "sc braga": "Брага",
  "braga": "Брага",
  "liberia u20": "Либерия U20",
  "gambia u20": "Гамбия U20",
  "dinamo zagreb": "Динамо Загреб",
  "marseille": "Марсель",
  "nec nijmegen": "НЕК Неймеген",
  "levski sofia": "Левски София",
  "pfc levski sofia": "Левски София",
  "brann": "Бранн",
  "lincoln red imps": "Линкольн Ред Импс",
  "lincoln red imps fc": "Линкольн Ред Импс",
  "heart of midlothian": "Хартс",
  "fc nordsjaelland": "Норшелланн",
  "nordsjaelland": "Норшелланн",
  "fremad amager": "Фремад Амагер",
  "nykobing fc": "Нюкёбинг",
  "naestved": "Нествед",
  "b 93": "Б-93 Копенгаген",
  "estudiantes lp": "Эстудиантес",
  "estudiantes l.p.": "Эстудиантес",
  "flamengo": "Фламенго",

  // --- Англия ---
  "arsenal": "Арсенал",
  "arsenal fc": "Арсенал",
  "aston villa": "Астон Вилла",
  "chelsea": "Челси",
  "chelsea fc": "Челси",
  "everton": "Эвертон",
  "fulham": "Фулхэм",
  "ipswich": "Ипсвич",
  "ipswich town": "Ипсвич",
  "leicester": "Лестер",
  "leicester city": "Лестер",
  "liverpool": "Ливерпуль",
  "liverpool fc": "Ливерпуль",
  "manchester city": "Манчестер Сити",
  "man city": "Манчестер Сити",
  "manchester united": "Манчестер Юнайтед",
  "man united": "Манчестер Юнайтед",
  "newcastle": "Ньюкасл",
  "newcastle united": "Ньюкасл",
  "nottingham forest": "Ноттингем Форест",
  "southampton": "Саутгемптон",
  "tottenham": "Тоттенхэм",
  "tottenham hotspur": "Тоттенхэм",
  "west ham": "Вест Хэм",
  "west ham united": "Вест Хэм",
  "wolverhampton": "Вулверхэмптон",
  "wolves": "Вулверхэмптон",
  "leeds": "Лидс",
  "leeds united": "Лидс",
  "burnley": "Бёрнли",
  "sheffield united": "Шеффилд Юнайтед",
  "luton town": "Лутон Таун",
  "luton": "Лутон",
  "middlesbrough": "Мидлсбро",
  "norwich city": "Норвич",
  "norwich": "Норвич",
  "west bromwich": "Вест Бромвич",
  "west brom": "Вест Бромвич",
  "watford": "Уотфорд",
  "stoke city": "Сток Сити",
  "blackburn rovers": "Блэкберн",
  "cardiff city": "Кардифф",
  "qpr": "КПР",
  "queens park rangers": "КПР",
  "hull city": "Халл Сити",
  "coventry city": "Ковентри",
  "preston north end": "Престон",
  "derby county": "Дерби Каунти",
  "portsmouth": "Портсмут",
  "swansea city": "Суонси",
  "millwall": "Миллуолл",

  // --- Испания ---
  "real madrid": "Реал Мадрид",
  "barcelona": "Барселона",
  "fc barcelona": "Барселона",
  "atletico madrid": "Атлетико Мадрид",
  "athletic bilbao": "Атлетик Бильбао",
  "athletic club": "Атлетик Бильбао",
  "valencia": "Валенсия",
  "sevilla": "Севилья",
  "villarreal": "Вильярреал",
  "real betis": "Реал Бетис",
  "betis": "Бетис",
  "osasuna": "Осасуна",
  "mallorca": "Мальорка",
  "rayo vallecano": "Райо Вальекано",
  "girona": "Жирона",
  "alaves": "Алавес",
  "deportivo alaves": "Алавес",
  "las palmas": "Лас-Пальмас",
  "leganes": "Леганес",
  "valladolid": "Вальядолид",
  "real valladolid": "Вальядолид",
  "espanyol": "Эспаньол",
  "cadiz": "Кадис",
  "granada": "Гранада",
  "almeria": "Альмерия",
  "deportivo la coruna": "Депортиво",
  "deportivo la coruña": "Депортиво",
  "levante": "Леванте",
  "sporting gijon": "Спортинг Хихон",
  "elche": "Эльче",
  "zaragoza": "Сарагоса",
  "real zaragoza": "Сарагоса",
  "tenerife": "Тенерифе",
  "malaga": "Малага",
  "eibar": "Эйбар",
  "huesca": "Уэска",
  "racing santander": "Расинг Сантандер",
  "burgos": "Бургос",
  "albacete": "Альбасете",
  "cartagena": "Картахена",
  "mirandes": "Мирандес",
  "ferrol": "Расинг Ферроль",
  "castellon": "Кастельон",
  "cordoba": "Кордова",
  "elda": "Эльденсе",
  "eldense": "Эльденсе",

  // --- Италия ---
  "inter": "Интер",
  "inter milan": "Интер",
  "internazionale": "Интер",
  "roma": "Рома",
  "as roma": "Рома",
  "lazio": "Лацио",
  "ss lazio": "Лацио",
  "napoli": "Наполи",
  "ssc napoli": "Наполи",
  "fiorentina": "Фиорентина",
  "bologna": "Болонья",
  "torino": "Торино",
  "monza": "Монца",
  "genoa": "Дженоа",
  "cagliari": "Кальяри",
  "udinese": "Удинезе",
  "verona": "Верона",
  "hellas verona": "Верона",
  "parma": "Парма",
  "como": "Комо",
  "empoli": "Эмполи",
  "venezia": "Венеция",
  "lecce": "Лечче",
  "sassuolo": "Сассуоло",
  "frosinone": "Фрозиноне",
  "salernitana": "Салернитана",
  "palermo": "Палермо",
  "sampdoria": "Сампдория",
  "bari": "Бари",
  "brescia": "Брешиа",
  "cremonese": "Кремонезе",
  "spezia": "Специя",
  "cesena": "Чезена",
  "pisa": "Пиза",
  "catanzaro": "Катандзаро",
  "sudtirol": "Зюдтироль",
  "modena": "Модена",
  "reggiana": "Реджана",
  "cosenza": "Козенца",
  "carrarese": "Каррарезе",
  "mantova": "Мантова",
  "juve stabia": "Юве Стабия",

  // --- Германия ---
  "borussia dortmund": "Боруссия Дортмунд",
  "dortmund": "Боруссия Дортмунд",
  "bvb": "Боруссия Дортмунд",
  "rb leipzig": "РБ Лейпциг",
  "leipzig": "РБ Лейпциг",
  "eintracht frankfurt": "Айнтрахт Франкфурт",
  "frankfurt": "Айнтрахт Франкфурт",
  "vfb stuttgart": "Штутгарт",
  "stuttgart": "Штутгарт",
  "borussia monchengladbach": "Боруссия Мёнхенгладбах",
  "monchengladbach": "Боруссия Мёнхенгладбах",
  "wolfsburg": "Вольфсбург",
  "vfl wolfsburg": "Вольфсбург",
  "werder bremen": "Вердер",
  "werder": "Вердер",
  "augsburg": "Аугсбург",
  "fc augsburg": "Аугсбург",
  "mainz 05": "Майнц",
  "mainz": "Майнц",
  "union berlin": "Унион Берлин",
  "heidenheim": "Хайденхайм",
  "st. pauli": "Санкт-Паули",
  "st pauli": "Санкт-Паули",
  "holstein kiel": "Хольштайн Киль",
  "bochum": "Бохум",
  "vfl bochum": "Бохум",
  "koln": "Кёльн",
  "1. fc koln": "Кёльн",
  "hertha bsc": "Герта",
  "hertha": "Герта",
  "hamburg": "Гамбург",
  "hamburger sv": "Гамбург",
  "schalke 04": "Шальке",
  "schalke": "Шальке",
  "fortuna dusseldorf": "Фортуна Дюссельдорф",
  "hannover 96": "Ганновер",
  "karlsruher sc": "Карлсруэ",
  "nurnberg": "Нюрнберг",
  "kaiserslautern": "Кайзерслаутерн",
  "paderborn": "Падерборн",
  "greuther furth": "Гройтер Фюрт",
  "darmstadt 98": "Дармштадт",

  // --- Франция ---
  "psg": "ПСЖ",
  "paris saint-germain": "ПСЖ",
  "paris sg": "ПСЖ",
  "lille": "Лилль",
  "losc lille": "Лилль",
  "lens": "Ланс",
  "rc lens": "Ланс",
  "nice": "Ницца",
  "ogc nice": "Ницца",
  "reims": "Реймс",
  "stade de reims": "Реймс",
  "strasbourg": "Страсбур",
  "rc strasbourg": "Страсбур",
  "toulouse": "Тулуза",
  "nantes": "Нант",
  "fc nantes": "Нант",
  "auxerre": "Осер",
  "le havre": "Гавр",
  "brest": "Брест",
  "stade brestois": "Брест",
  "saint-etienne": "Сент-Этьен",
  "angers": "Анже",
  "montpellier": "Монпелье",
  "lorient": "Лорьян",
  "metz": "Мец",
  "clermont": "Клермон",
  "bordeaux": "Бордо",

  // --- Португалия, Нидерланды, Турция ---
  "porto": "Порту",
  "fc porto": "Порту",
  "sporting cp": "Спортинг",
  "sporting lisbon": "Спортинг",
  "vitoria guimaraes": "Витория Гимарайнш",
  "vitoria sc": "Витория Гимарайнш",
  "boavista": "Боавишта",
  "famalicao": "Фамаликан",
  "rio ave": "Риу Аве",
  "estoril": "Эшторил",
  "arouca": "Арока",
  "gil vicente": "Жил Висенте",
  "farense": "Фаренсе",
  "nacional madeira": "Насьонал",
  "psv": "ПСВ",
  "psv eindhoven": "ПСВ",
  "feyenoord": "Фейеноорд",
  "utrecht": "Утрехт",
  "heerenveen": "Херенвен",
  "sparta rotterdam": "Спарта Роттердам",
  "go ahead eagles": "Гоу Эхед Иглз",
  "fortuna sittard": "Фортуна Ситтард",
  "pec zwolle": "Зволле",
  "almere city": "Алмере Сити",
  "willem ii": "Виллем II",
  "groningen": "Гронинген",
  "rkc waalwijk": "Валвейк",
  "galatasaray": "Галатасарай",
  "fenerbahce": "Фенербахче",
  "fenerbahçe": "Фенербахче",
  "basaksehir": "Башакшехир",
  "kasimpasa": "Касымпаша",
  "antalyaspor": "Антальяспор",
  "sivasspor": "Сивасспор",
  "alanyaspor": "Аланьяспор",
  "kayserispor": "Кайсериспор",
  "konyaspor": "Коньяспор",
  "rizespor": "Ризеспор",
  "gaziantep": "Газиантеп",
  "goztepe": "Гёзтепе",
  "eyupspor": "Эюпспор",
  "bodrum": "Бодрум",
  "adana demirspor": "Адана Демирспор",
  "samsunspor": "Самсунспор",

  // --- Россия (РПЛ, Первая лига, КХЛ) ---
  "zenit": "Зенит",
  "spartak moscow": "Спартак Москва",
  "cska moscow": "ЦСКА Москва",
  "dynamo moscow": "Динамо Москва",
  "lokomotiv moscow": "Локомотив Москва",
  "krasnodar": "Краснодар",
  "rostov": "Ростов",
  "rubin kazan": "Рубин",
  "krylya sovetov": "Крылья Советов",
  "akhmat grozny": "Ахмат",
  "fakel voronezh": "Факел",
  "orenburg": "Оренбург",
  "pari nn": "Пари НН",
  "nizhny novgorod": "Пари НН",
  "khimki": "Химки",
  "dinamo makhachkala": "Динамо Махачкала",
  "akron tolyatti": "Акрон",
  "baltika": "Балтика",
  "sochi": "Сочи",
  "ural": "Урал",
  "ska st petersburg": "СКА",
  "ska": "СКА",
  "metallurg magnitogorsk": "Металлург Магнитогорск",
  "avangard omsk": "Авангард",
  "ak bars kazan": "Ак Барс",
  "salavat yulaev": "Салават Юлаев",
  "traktor chelyabinsk": "Трактор",
  "avtomobilist": "Автомобилист",
  "severstal": "Северсталь",
  "torpedo nizhny novgorod": "Торпедо НН",
  "amur khabarovsk": "Амур",
  "sibir novosibirsk": "Сибирь",
  "barys": "Барыс",
  "dinamo minsk": "Динамо Минск",
  "neftekhimik": "Нефтехимик",
  "lada togliatti": "Лада",
  "admirall vladivostok": "Адмирал",
  "vityaz moscow": "Витязь",
  "kunlun red star": "Куньлунь Ред Стар",

  // --- НХЛ ---
  "new york rangers": "Нью-Йорк Рейнджерс",
  "edmonton oilers": "Эдмонтон Ойлерз",
  "florida panthers": "Флорида Пантерз",
  "tampa bay lightning": "Тампа-Бэй Лайтнинг",
  "carolina hurricanes": "Каролина Харрикейнз",
  "colorado avalanche": "Колорадо Эвеланш",
  "dallas stars": "Даллас Старз",
  "vegas golden knights": "Вегас Голден Найтс",
  "boston bruins": "Бостон Брюинз",
  "toronto maple leafs": "Торонто Мейпл Лифс",
  "vancouver canucks": "Ванкувер Кэнакс",
  "winnipeg jets": "Виннипег Джетс",
  "los angeles kings": "Лос-Анджелес Кингз",
  "washington capitals": "Вашингтон Кэпиталз",
  "nashville predators": "Нэшвилл Предаторз",
  "pittsburgh penguins": "Питтсбург Пингвинз",
  "detroit red wings": "Детройт Ред Уингз",
  "st. louis blues": "Сент-Луис Блюз",
  "new jersey devils": "Нью-Джерси Девилз",
  "minnesota wild": "Миннесота Уайлд",
  "philadelphia flyers": "Филадельфия Флайерз",
  "calgary flames": "Калгари Флэймз",
  "seattle kraken": "Сиэтл Кракен",
  "ottawa senators": "Оттава Сенаторз",
  "montreal canadiens": "Монреаль Канадиенс",
  "buffalo sabres": "Баффало Сейбрз",
  "arizona coyotes": "Аризона Койотис",
  "utah hockey club": "Юта ХК",
  "anaheim ducks": "Анахайм Дакс",
  "chicago blackhawks": "Чикаго Блэкхокс",
  "san jose sharks": "Сан-Хосе Шаркс",
  "columbus blue jackets": "Коламбус Блю Джекетс",

  // --- НБА ---
  "boston celtics": "Бостон Селтикс",
  "denver nuggets": "Денвер Наггетс",
  "minnesota timberwolves": "Миннесота Тимбервулвз",
  "oklahoma city thunder": "Оклахома-Сити Тандер",
  "dallas mavericks": "Даллас Маверикс",
  "new york knicks": "Нью-Йорк Никс",
  "milwaukee bucks": "Милуоки Бакс",
  "philadelphia 76ers": "Филадельфия Севенти Сиксерс",
  "los angeles clippers": "Лос-Анджелес Клипперс",
  "phoenix suns": "Финикс Санз",
  "indiana pacers": "Индиана Пэйсерс",
  "cleveland cavaliers": "Кливленд Кавальерс",
  "los angeles lakers": "Лос-Анджелес Лейкерс",
  "orlando magic": "Орландо Мэджик",
  "golden state warriors": "Голден Стэйт Уорриорз",
  "miami heat": "Майами Хит",
  "sacramento kings": "Сакраменто Кингз",
  "new orleans pelicans": "Нью-Орлеан Пеликанс",
  "chicago bulls": "Чикаго Буллз",
  "atlanta hawks": "Атланта Хокс",
  "houston rockets": "Хьюстон Рокетс",
  "utah jazz": "Юта Джаз",
  "brooklyn nets": "Бруклин Нетс",
  "toronto raptors": "Торонто Рэпторс",
  "memphis grizzlies": "Мемфис Гриззлис",
  "san antonio spurs": "Сан-Антонио Спёрс",
  "charlotte hornets": "Шарлотт Хорнетс",
  "portland trail blazers": "Портленд Трэйл Блэйзерс",
  "washington wizards": "Вашингтон Уизардс",
  "detroit pistons": "Детройт Пистонс",

  // --- Южная Америка ---
  "river plate": "Ривер Плейт",
  "boca juniors": "Бока Хуниорс",
  "racing club": "Расинг Авельянеда",
  "independiente": "Индепендьенте",
  "san lorenzo": "Сан-Лоренсо",
  "velez sarsfield": "Велес Сарсфилд",
  "vélez sársfield": "Велес Сарсфилд",
  "talleres": "Тальерес",
  "rosario central": "Росарио Сентраль",
  "newell's old boys": "Ньюэллс Олд Бойз",
  "lanus": "Ланус",
  "estudiantes": "Эстудиантес",
  "argentinos juniors": "Архентинос Хуниорс",
  "godoy cruz": "Годой-Крус",
  "belgrano": "Бельграно",
  "instituto": "Институто",
  "platense": "Платенсе",
  "barracas central": "Барракас Сентраль",
  "banfield": "Банфилд",
  "tigre": "Тигре",
  "sarmiento": "Сармьенто",
  "central cordoba": "Сентраль Кордова",
  "deportivo riestra": "Депортиво Риестра",
  "independiente rivadavia": "Индепендьенте Ривадавия",
  "atletico tucuman": "Атлетико Тукуман",
  "atlético tucumán": "Атлетико Тукуман",
  "colon": "Колон",
  "colon de santa fe": "Колон",
  "palmeiras": "Палмейрас",
  "sao paulo": "Сан-Паулу",
  "são paulo": "Сан-Паулу",
  "corinthians": "Коринтианс",
  "internacional": "Интернасьонал",
  "gremio": "Гремио",
  "grêmio": "Гремио",
  "atletico mineiro": "Атлетико Минейро",
  "atletico-mg": "Атлетико Минейро",
  "fluminense": "Флуминенсе",
  "cruzeiro": "Крузейро",
  "botafogo": "Ботафого",
  "athletico paranaense": "Атлетико Паранаэнсе",
  "fortaleza": "Форталеза",
  "bahia": "Баия",
  "vasco da gama": "Васко да Гама",
  "juventude": "Жувентуде",
  "criciuma": "Крисиума",
  "vitoria": "Витория Салвадор",
  "cuiaba": "Куяба",
  "atletico goianiense": "Атлетико Гоияниенсе",
  "chapecoense": "Шапекоэнсе",
  "sport recife": "Спорт Ресифи",
  "santos": "Сантос",
  "ceara": "Сеара",
  "coritiba": "Коритиба",
  "goias": "Гояс",
  "avai": "Аваи",
  "vila nova": "Вила Нова",
  "mirassol": "Мирасол",
  "novorizontino": "Новоризонтино",
  "operario": "Операрио",
  "amazonas": "Амазонас",
  "crb": "КРБ",
  "paysandu": "Пайсанду",
  "botafogo-sp": "Ботафого СП",
  "chapecoense-sc": "Шапекоэнсе",
  "brusque": "Бруски",
  "ituano": "Итуано",
  "guarani": "Гуарани Кампинас",
  "penarol": "Пеньяроль",
  "peñarol": "Пеньяроль",
  "nacional": "Насьональ Монтевидео",
  "danubio": "Данубио",
  "defensor sporting": "Дефенсор Спортинг",
  "liverpool montevideo": "Ливерпуль Монтевидео",
  "wanderers": "Монтевидео Уондерерс",
  "cerro": "Серро",
  "boston river": "Бостон Ривер",
  "river plate montevideo": "Ривер Плейт Монтевидео",
  "racing montevideo": "Расинг Монтевидео",
  "progreso": "Прогресо",
  "fenix": "Феникс",
  "deportivo maldonado": "Депортиво Мальдонадо",
  "miramar misiones": "Мирамар Мисьонес",
  "rampla juniors": "Рампла Хуниорс",
  "central espanol": "Сентраль Эспаньол"
};

// Таблица транслитерации латиницы в русские буквы для неизвестных клубов
const PHONETIC_RULES = [
  [/tion\b/gi, 'шн'],
  [/chester\b/gi, 'честер'],
  [/hampton\b/gi, 'хэмптон'],
  [/mouth\b/gi, 'мут'],
  [/pool\b/gi, 'пуль'],
  [/field\b/gi, 'филд'],
  [/bridge\b/gi, 'бридж'],
  [/brough\b/gi, 'бро'],
  [/burgh\b/gi, 'бург'],
  [/burg\b/gi, 'бург'],
  [/ville\b/gi, 'виль'],
  [/town\b/gi, 'Таун'],
  [/city\b/gi, 'Сити'],
  [/united\b/gi, 'Юнайтед'],
  [/rovers\b/gi, 'Роверс'],
  [/rangers\b/gi, 'Рейнджерс'],
  [/wanderers\b/gi, 'Уондерерс'],
  [/albion\b/gi, 'Альбион'],
  [/athletic\b/gi, 'Атлетик'],
  [/atletico\b/gi, 'Атлетико'],
  [/sporting\b/gi, 'Спортинг'],
  [/olympic\b/gi, 'Олимпик'],
  [/olympique\b/gi, 'Олимпик'],
  [/dynamo\b/gi, 'Динамо'],
  [/dinamo\b/gi, 'Динамо'],
  [/sparta\b/gi, 'Спарта'],
  [/slavia\b/gi, 'Славия'],
  [/viktoria\b/gi, 'Виктория'],
  [/victoria\b/gi, 'Виктория'],
  [/real\b/gi, 'Реал'],
  [/racing\b/gi, 'Расинг'],
  [/central\b/gi, 'Сентраль'],
  [/deportivo\b/gi, 'Депортиво'],
  [/independiente\b/gi, 'Индепендьенте'],
  [/universidad\b/gi, 'Универсидад'],
  [/universitario\b/gi, 'Университарио'],
  [/alianza\b/gi, 'Альянса'],
  [/sh/gi, 'ш'],
  [/ch/gi, 'ч'],
  [/zh/gi, 'ж'],
  [/th/gi, 'т'],
  [/ph/gi, 'ф'],
  [/kh/gi, 'х'],
  [/ts/gi, 'ц'],
  [/ya/gi, 'я'],
  [/yu/gi, 'ю'],
  [/yo/gi, 'ё'],
  [/ye/gi, 'е'],
  [/qu/gi, 'кв'],
  [/ck/gi, 'к'],
  [/oo/gi, 'у'],
  [/ee/gi, 'и'],
  [/ea/gi, 'и'],
  [/ai/gi, 'ай'],
  [/ay/gi, 'ей'],
  [/ey/gi, 'ей'],
  [/oi/gi, 'ой'],
  [/oy/gi, 'ой'],
  [/au/gi, 'ау'],
  [/aw/gi, 'о'],
  [/ow/gi, 'оу'],
  [/a/gi, 'а'],
  [/b/gi, 'б'],
  [/c([eiy])/gi, 'с$1'],
  [/c/gi, 'к'],
  [/d/gi, 'д'],
  [/e/gi, 'е'],
  [/f/gi, 'ф'],
  [/g([eiy])/gi, 'дж$1'],
  [/g/gi, 'г'],
  [/h/gi, 'х'],
  [/i/gi, 'и'],
  [/j/gi, 'дж'],
  [/k/gi, 'к'],
  [/l/gi, 'л'],
  [/m/gi, 'м'],
  [/n/gi, 'н'],
  [/o/gi, 'о'],
  [/p/gi, 'п'],
  [/r/gi, 'р'],
  [/s/gi, 'с'],
  [/t/gi, 'т'],
  [/u/gi, 'у'],
  [/v/gi, 'в'],
  [/w/gi, 'в'],
  [/x/gi, 'кс'],
  [/y/gi, 'и'],
  [/z/gi, 'з']
];

/**
 * Фонетическая транслитерация неизвестных латинских имен в кириллицу
 */
function phoneticTransliterate(latinStr) {
  let res = latinStr;
  for (const [pattern, replacement] of PHONETIC_RULES) {
    res = res.replace(pattern, replacement);
  }
  // Капитализация первой буквы каждого слова
  return res.split(' ').map(w => w ? w[0].toUpperCase() + w.slice(1) : '').join(' ');
}

/**
 * Главная функция: возвращает красивое русское название команды.
 * Если уже на русском — возвращает аккуратно отформатированное имя.
 * Если на латинице — сначала ищет в словаре, затем использует умную транслитерацию.
 */
export function toRussianTeam(name) {
  if (!name || typeof name !== 'string') return '';
  const trimmed = name.trim();
  if (!trimmed) return '';

  // 1. Проверяем, если строка уже полностью или в основном на русском
  const cyrillicMatches = trimmed.match(/[а-яёА-ЯЁ]/g) || [];
  if (cyrillicMatches.length >= trimmed.length * 0.45) {
    return trimmed;
  }

  // 2. Очищаем латинские клубные суффиксы для поиска в словаре
  let clean = trimmed.toLowerCase();
  clean = clean.replace(/^(fc|fk|sc|cf|ac|bc|cd|ca|pfc|gnk|rsc|sk|sl)\s+/i, '').trim();
  clean = clean.replace(/\s+(fc|fk|tc|sc|cf|bc|jk|lp|u20|u19|u21|res|reserves|b)$/i, '').trim();

  // Прямой поиск в словаре
  if (TEAMS_RU_MAP[trimmed.toLowerCase()]) {
    return TEAMS_RU_MAP[trimmed.toLowerCase()];
  }
  if (TEAMS_RU_MAP[clean]) {
    return TEAMS_RU_MAP[clean];
  }

  // Нечеткий перебор словаря
  for (const [key, ruVal] of Object.entries(TEAMS_RU_MAP)) {
    if (key.length >= 4 && (clean === key || clean.includes(key) || key.includes(clean))) {
      return ruVal;
    }
  }

  // 3. Фонетическая транслитерация (умный автоперевод)
  return phoneticTransliterate(trimmed);
}

/**
 * Превращает пару команд "Team 1 vs Team 2" или "Team 1 - Team 2" в русские названия
 */
export function toRussianMatchName(matchName) {
  if (!matchName) return '';
  if (matchName.includes(' vs ')) {
    const [h, a] = matchName.split(' vs ');
    return `${toRussianTeam(h)} — ${toRussianTeam(a)}`;
  }
  if (matchName.includes(' - ')) {
    const [h, a] = matchName.split(' - ');
    return `${toRussianTeam(h)} — ${toRussianTeam(a)}`;
  }
  return toRussianTeam(matchName);
}

/**
 * Словарь русских названий лиг и чемпионатов
 */
export const LEAGUES_RU_MAP = {
  // Международные и еврокубки
  "soccer_uefa_champs_league": "Лига чемпионов УЕФА",
  "champs_league": "Лига чемпионов УЕФА",
  "champions_league": "Лига чемпионов УЕФА",
  "лига чемпионов": "Лига чемпионов УЕФА",
  "uefa champions league": "Лига чемпионов УЕФА",
  "soccer_uefa_europa_league": "Лига Европы УЕФА",
  "europa_league": "Лига Европы УЕФА",
  "лига европы": "Лига Европы УЕФА",
  "uefa europa league": "Лига Европы УЕФА",
  "soccer_uefa_conference_league": "Лига конференций УЕФА",
  "conference_league": "Лига конференций УЕФА",
  "лига конференций": "Лига конференций УЕФА",
  "uefa conference league": "Лига конференций УЕФА",
  "nations_league": "Лига наций УЕФА",
  "copa_libertadores": "Кубок Либертадорес",
  "copa_sudamericana": "Южноамериканский кубок",

  // Топ-5 Европы
  "soccer_epl": "АПЛ • Чемпионат Англии",
  "epl": "АПЛ • Чемпионат Англии",
  "premier_league": "АПЛ • Чемпионат Англии",
  "english premier league": "АПЛ • Чемпионат Англии",
  "championship": "Чемпионшип • Англия",
  "soccer_spain_la_liga": "Ла Лига • Чемпионат Испании",
  "la_liga": "Ла Лига • Чемпионат Испании",
  "laliga": "Ла Лига • Чемпионат Испании",
  "spain_la_liga": "Ла Лига • Чемпионат Испании",
  "segunda": "Сегунда • Испания",
  "soccer_italy_serie_a": "Серия А • Чемпионат Италии",
  "serie_a": "Серия А • Чемпионат Италии",
  "italy_serie_a": "Серия А • Чемпионат Италии",
  "serie_b": "Серия B • Чемпионат Италии",
  "soccer_germany_bundesliga": "Бундеслига • Чемпионат Германии",
  "bundesliga": "Бундеслига • Чемпионат Германии",
  "germany_bundesliga": "Бундеслига • Чемпионат Германии",
  "bundesliga2": "Вторая Бундеслига • Германия",
  "soccer_france_ligue_one": "Лига 1 • Чемпионат Франции",
  "ligue_1": "Лига 1 • Чемпионат Франции",
  "france_ligue_one": "Лига 1 • Чемпионат Франции",
  "ligue_2": "Лига 2 • Чемпионат Франции",

  // Россия
  "soccer_russia_premier_league": "РПЛ • Чемпионат России",
  "rpl": "РПЛ • Чемпионат России",
  "рпл": "РПЛ • Чемпионат России",
  "russia_premier_league": "РПЛ • Чемпионат России",
  "fnl": "Первая лига • Россия",
  "кубок россии": "Кубок России",

  // Хоккей
  "icehockey_nhl": "НХЛ • Хоккей",
  "nhl": "НХЛ • Хоккей",
  "icehockey_khl": "КХЛ • Хоккей",
  "khl": "КХЛ • Хоккей",
  "vhl": "ВХЛ • Россия",
  "mhl": "МХЛ • Россия",

  // Баскетбол
  "basketball_nba": "НБА • Баскетбол",
  "nba": "НБА • Баскетбол",
  "basketball_euroleague": "Евролига • Баскетбол",
  "euroleague": "Евролига • Баскетбол",
  "vtb": "Единая лига ВТБ",

  // Другие
  "zulubet line": "Европейские чемпионаты",
  "eredivisie": "Эредивизи • Чемпионат Нидерландов",
  "primeira_liga": "Примейра • Чемпионат Португалии",
  "super_lig": "Суперлига • Чемпионат Турции",
  "belgium_first_div": "Про-Лига • Чемпионат Бельгии",
  "mls": "МЛС • Чемпионат США",
  "brasileirao": "Серия А • Чемпионат Бразилии"
};

/**
 * Преобразует любую системную строку лиги в презентабельный русский вид
 */
export function toRussianLeague(league = '', countryName = '') {
  if (!league) return countryName || 'Чемпионат';
  const low = league.toLowerCase().trim();

  // Прямой поиск в словаре
  if (LEAGUES_RU_MAP[low]) {
    return LEAGUES_RU_MAP[low];
  }

  // Нечеткий перебор
  for (const [key, ruVal] of Object.entries(LEAGUES_RU_MAP)) {
    if (low.includes(key)) {
      return ruVal;
    }
  }

  // Очистка от технических суффиксов
  const clean = league
    .replace(/^soccer_/i, '')
    .replace(/^icehockey_/i, '')
    .replace(/^basketball_/i, '')
    .replace(/_/g, ' ')
    .trim();

  if (countryName) {
    return `${clean} • ${countryName}`;
  }
  return clean || 'Чемпионат';
}

/**
 * Единый классификатор видов спорта (1-в-1 с бэкендом).
 */
export function getGenericSport(s = '') {
  const low = (s || '').toLowerCase().trim();
  if (['mma', 'ufc', 'bellator', 'boxing', 'martial'].some(x => low.includes(x))) return 'MMA';
  if (['tennis', 'atp', 'wta', 'itf'].some(x => low.includes(x))) return 'Tennis';
  if (['basketball', 'nba', 'euroleague', 'vtb', 'acb', 'nbl'].some(x => low.includes(x))) return 'Basketball';
  if (!low.includes('veikkausliiga') && ['hockey', 'nhl', 'khl', 'ahl', 'shl', 'liiga', 'mestis', 'vhl'].some(x => low.includes(x))) return 'Hockey';
  if (['nfl', 'ncaaf', 'american football', 'afl'].some(x => low.includes(x))) return 'American Football';
  if (['esport', 'dota', 'cs:go', 'cs2', 'counter-strike', 'league of legends', 'valorant'].some(x => low.includes(x))) return 'Esports';
  if (['baseball', 'mlb', 'kbo', 'npb'].some(x => low.includes(x))) return 'Baseball';
  if (['cricket', 'twenty20', 'one day international', 't20'].some(x => low.includes(x))) return 'Cricket';
  if ([
    'football', 'soccer', 'uefa', 'champions league', 'europa league', 'conference league',
    'la liga', 'epl', 'premier', 'serie', 'série', 'bundesliga', 'ligue', 'eredivisie', 'superliga',
    'ekstraklasa', 'eliteserien', 'allsvenskan', 'championship', 'copa', 'mls', 'primeira'
  ].some(x => low.includes(x))) return 'Football';
  return 'Football'; // По умолчанию для командных видов
}

/**
 * Получение текущей локальной даты (YYYY-MM-DD) без сдвига в UTC
 */
export function getLocalDateString(dateInput = new Date()) {
  const d = dateInput instanceof Date ? dateInput : new Date(dateInput);
  if (isNaN(d.getTime())) return new Date().toISOString().split('T')[0];
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
