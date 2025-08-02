/**
 * Научно обоснованный парфюмерный квиз v3.0
 * Основан на Edwards Fragrance Wheel (1983-2010) и психологических исследованиях
 * 15 вопросов по 5 блокам для точного профилирования
 */

class PerfumeQuiz {
    constructor() {
        this.currentQuestion = 0;
        this.answers = {};
        this.profile = {
            demographic: {},
            psychological: {},
            lifestyle: {},
            sensory: {},
            emotional: {}
        };
    }

    // Структура квиза: 15 вопросов по блокам
    questions = [
        // БЛОК 1: ДЕМОГРАФИЧЕСКИЙ (2 вопроса)
        {
            id: 'gender',
            block: 'demographic',
            type: 'single',
            text: 'Для кого предназначен аромат?',
            options: [
                {
                    text: 'Для меня (женщина)',
                    value: 'female',
                    keywords: ['женский', 'feminine', 'floral', 'delicate']
                },
                {
                    text: 'Для меня (мужчина)',
                    value: 'male',
                    keywords: ['мужской', 'masculine', 'woody', 'strong']
                },
                {
                    text: 'Унисекс',
                    value: 'unisex',
                    keywords: ['унисекс', 'unisex', 'neutral', 'balanced']
                }
            ]
        },
        {
            id: 'age_experience',
            block: 'demographic',
            type: 'single',
            text: 'Ваш опыт с парфюмерией?',
            options: [
                {
                    text: 'Новичок (первые ароматы)',
                    value: 'beginner',
                    keywords: ['легкий', 'простой', 'классический', 'популярный', 'безопасный']
                },
                {
                    text: 'Имею базовый опыт',
                    value: 'intermediate',
                    keywords: ['современный', 'трендовый', 'качественный', 'сбалансированный']
                },
                {
                    text: 'Продвинутый (коллекционер)',
                    value: 'advanced',
                    keywords: ['нишевый', 'эксклюзивный', 'сложный', 'уникальный', 'артистический']
                }
            ]
        },

        // БЛОК 2: ПСИХОЛОГИЧЕСКИЙ (3 вопроса)
        {
            id: 'personality_type',
            block: 'psychological',
            type: 'single',
            text: 'Какой тип личности вам ближе?',
            options: [
                {
                    text: 'Романтик',
                    value: 'romantic',
                    keywords: ['романтичный', 'чувственный', 'нежный', 'floral', 'rose', 'jasmine']
                },
                {
                    text: 'Интеллектуал',
                    value: 'intellectual',
                    keywords: ['сложный', 'утонченный', 'изысканный', 'green', 'herbaceous']
                },
                {
                    text: 'Экстраверт',
                    value: 'extrovert',
                    keywords: ['яркий', 'заметный', 'bold', 'oriental', 'spicy']
                },
                {
                    text: 'Интроверт',
                    value: 'introvert',
                    keywords: ['спокойный', 'деликатный', 'subtle', 'woody', 'musky']
                },
                {
                    text: 'Логик-аналитик',
                    value: 'analytical',
                    keywords: ['структурированный', 'чистый', 'minimalistic', 'aquatic', 'ozonic']
                }
            ]
        },
        {
            id: 'lifestyle',
            block: 'psychological',
            type: 'single',
            text: 'Опишите ваш образ жизни:',
            options: [
                {
                    text: 'Активный и динамичный',
                    value: 'active',
                    keywords: ['энергичный', 'спортивный', 'fresh', 'citrus', 'energizing']
                },
                {
                    text: 'Спокойный и размеренный',
                    value: 'calm',
                    keywords: ['расслабляющий', 'мягкий', 'comforting', 'vanilla', 'amber']
                },
                {
                    text: 'Творческий и артистичный',
                    value: 'creative',
                    keywords: ['креативный', 'необычный', 'artistic', 'incense', 'patchouli']
                },
                {
                    text: 'Деловой и профессиональный',
                    value: 'professional',
                    keywords: ['строгий', 'элегантный', 'sophisticated', 'cedar', 'sandalwood']
                }
            ]
        },
        {
            id: 'usage_time',
            block: 'psychological',
            type: 'multiple',
            text: 'В какое время дня планируете использовать аромат?',
            options: [
                {
                    text: 'Утром и днем',
                    value: 'day',
                    keywords: ['дневной', 'light', 'fresh', 'citrus', 'green']
                },
                {
                    text: 'Вечером',
                    value: 'evening',
                    keywords: ['вечерний', 'intense', 'oriental', 'woody', 'amber']
                },
                {
                    text: 'На особые случаи',
                    value: 'special',
                    keywords: ['праздничный', 'luxurious', 'sophisticated', 'oud', 'rare']
                },
                {
                    text: 'Универсально',
                    value: 'universal',
                    keywords: ['универсальный', 'versatile', 'balanced', 'moderate']
                }
            ]
        },

        // БЛОК 3: LIFESTYLE (4 вопроса)
        {
            id: 'occasions',
            block: 'lifestyle',
            type: 'multiple',
            text: 'Для каких случаев нужен аромат?',
            options: [
                {
                    text: 'Повседневная работа/учеба',
                    value: 'work',
                    keywords: ['офисный', 'деликатный', 'professional', 'clean', 'subtle']
                },
                {
                    text: 'Романтические встречи',
                    value: 'romantic',
                    keywords: ['соблазнительный', 'чувственный', 'seductive', 'rose', 'ylang-ylang']
                },
                {
                    text: 'Вечеринки и мероприятия',
                    value: 'party',
                    keywords: ['яркий', 'запоминающийся', 'party', 'gourmand', 'sweet']
                },
                {
                    text: 'Спорт и активность',
                    value: 'sport',
                    keywords: ['свежий', 'легкий', 'sport', 'aquatic', 'marine']
                },
                {
                    text: 'Отдых и релакс',
                    value: 'relaxation',
                    keywords: ['успокаивающий', 'комфортный', 'relaxing', 'lavender', 'chamomile']
                }
            ]
        },
        {
            id: 'style_preference',
            block: 'lifestyle',
            type: 'single',
            text: 'Ваш стиль в одежде:',
            options: [
                {
                    text: 'Классический и элегантный',
                    value: 'classic',
                    keywords: ['классический', 'элегантный', 'timeless', 'chypre', 'aldehydic']
                },
                {
                    text: 'Модный и трендовый',
                    value: 'trendy',
                    keywords: ['модный', 'современный', 'trendy', 'fruity', 'synthetic']
                },
                {
                    text: 'Casual и комфортный',
                    value: 'casual',
                    keywords: ['простой', 'комфортный', 'easy-going', 'cotton', 'clean']
                },
                {
                    text: 'Экстравагантный и яркий',
                    value: 'bold',
                    keywords: ['яркий', 'смелый', 'extravagant', 'leather', 'tobacco']
                }
            ]
        },
        {
            id: 'budget_category',
            block: 'lifestyle',
            type: 'single',
            text: 'Предпочтительная ценовая категория:',
            options: [
                {
                    text: 'Доступная (масс-маркет)',
                    value: 'mass_market',
                    keywords: ['популярный', 'доступный', 'commercial', 'mainstream']
                },
                {
                    text: 'Средняя (селективная)',
                    value: 'selective',
                    keywords: ['качественный', 'селективный', 'premium', 'boutique']
                },
                {
                    text: 'Высокая (люкс/нишевая)',
                    value: 'luxury',
                    keywords: ['люксовый', 'нишевый', 'luxury', 'exclusive', 'artisanal']
                }
            ]
        },
        {
            id: 'longevity_preference',
            block: 'lifestyle',
            type: 'single',
            text: 'Предпочтительная стойкость аромата:',
            options: [
                {
                    text: 'Легкий и ненавязчивый (2-4 часа)',
                    value: 'light',
                    keywords: ['легкий', 'деликатный', 'eau_de_cologne', 'citrus', 'aromatic']
                },
                {
                    text: 'Умеренной стойкости (4-6 часов)',
                    value: 'moderate',
                    keywords: ['умеренный', 'сбалансированный', 'eau_de_toilette', 'balanced']
                },
                {
                    text: 'Стойкий и насыщенный (8+ часов)',
                    value: 'long_lasting',
                    keywords: ['стойкий', 'насыщенный', 'eau_de_parfum', 'intense', 'heavy']
                }
            ]
        },

        // БЛОК 4: СЕНСОРНЫЙ (3 вопроса) - Edwards Fragrance Wheel
        {
            id: 'fragrance_families',
            block: 'sensory',
            type: 'multiple',
            text: 'Какие ароматические семейства вам нравятся? (Edwards Wheel)',
            options: [
                {
                    text: 'Цветочные (роза, жасмин, пион)',
                    value: 'floral',
                    keywords: ['floral', 'rose', 'jasmine', 'peony', 'lily', 'romantic']
                },
                {
                    text: 'Восточные/Амбровые (ваниль, амбра, мускус)',
                    value: 'oriental',
                    keywords: ['oriental', 'amber', 'vanilla', 'musk', 'resin', 'warm']
                },
                {
                    text: 'Древесные (сандал, кедр, дуб)',
                    value: 'woody',
                    keywords: ['woody', 'sandalwood', 'cedar', 'oak', 'pine', 'forest']
                },
                {
                    text: 'Свежие (цитрус, зеленые, водные)',
                    value: 'fresh',
                    keywords: ['fresh', 'citrus', 'green', 'aquatic', 'marine', 'clean']
                }
            ]
        },
        {
            id: 'intensity_preference',
            block: 'sensory',
            type: 'single',
            text: 'Предпочтительная интенсивность аромата:',
            options: [
                {
                    text: 'Деликатная и тонкая',
                    value: 'delicate',
                    keywords: ['деликатный', 'тонкий', 'subtle', 'soft', 'gentle']
                },
                {
                    text: 'Умеренная и сбалансированная',
                    value: 'moderate',
                    keywords: ['умеренный', 'сбалансированный', 'moderate', 'balanced']
                },
                {
                    text: 'Яркая и насыщенная',
                    value: 'intense',
                    keywords: ['яркий', 'насыщенный', 'intense', 'bold', 'powerful']
                }
            ]
        },
        {
            id: 'seasonal_preference',
            block: 'sensory',
            type: 'multiple',
            text: 'В какие сезоны планируете носить аромат?',
            options: [
                {
                    text: 'Весна',
                    value: 'spring',
                    keywords: ['весенний', 'свежий', 'green', 'floral', 'light']
                },
                {
                    text: 'Лето',
                    value: 'summer',
                    keywords: ['летний', 'легкий', 'citrus', 'aquatic', 'fresh']
                },
                {
                    text: 'Осень',
                    value: 'autumn',
                    keywords: ['осенний', 'теплый', 'spicy', 'woody', 'amber']
                },
                {
                    text: 'Зима',
                    value: 'winter',
                    keywords: ['зимний', 'согревающий', 'oriental', 'heavy', 'intense']
                }
            ]
        },

        // БЛОК 5: ЭМОЦИОНАЛЬНО-АССОЦИАТИВНЫЙ (3 вопроса)
        {
            id: 'desired_mood',
            block: 'emotional',
            type: 'multiple',
            text: 'Какие настроения и эмоции хотите передать?',
            options: [
                {
                    text: 'Уверенность и силу',
                    value: 'confidence',
                    keywords: ['уверенный', 'сильный', 'powerful', 'dominant', 'leader']
                },
                {
                    text: 'Романтику и нежность',
                    value: 'romance',
                    keywords: ['романтичный', 'нежный', 'romantic', 'tender', 'loving']
                },
                {
                    text: 'Элегантность и изысканность',
                    value: 'elegance',
                    keywords: ['элегантный', 'изысканный', 'sophisticated', 'refined', 'classy']
                },
                {
                    text: 'Энергию и жизнерадостность',
                    value: 'energy',
                    keywords: ['энергичный', 'жизнерадостный', 'energetic', 'vibrant', 'happy']
                },
                {
                    text: 'Спокойствие и гармонию',
                    value: 'calm',
                    keywords: ['спокойный', 'гармоничный', 'peaceful', 'serene', 'balanced']
                }
            ]
        },
        {
            id: 'scent_memories',
            block: 'emotional',
            type: 'multiple',
            text: 'Какие ароматические воспоминания вам приятны?',
            options: [
                {
                    text: 'Цветущий сад весной',
                    value: 'garden',
                    keywords: ['цветочный', 'природный', 'garden', 'blooming', 'natural']
                },
                {
                    text: 'Уютный дом с выпечкой',
                    value: 'home_comfort',
                    keywords: ['уютный', 'сладкий', 'gourmand', 'vanilla', 'caramel']
                },
                {
                    text: 'Прогулка по лесу',
                    value: 'forest',
                    keywords: ['лесной', 'древесный', 'forest', 'pine', 'earthy']
                },
                {
                    text: 'Морской берег',
                    value: 'ocean',
                    keywords: ['морской', 'свежий', 'marine', 'salty', 'breeze']
                },
                {
                    text: 'Восточный базар',
                    value: 'oriental_market',
                    keywords: ['восточный', 'пряный', 'spicy', 'exotic', 'incense']
                }
            ]
        },
        {
            id: 'color_associations',
            block: 'emotional',
            type: 'multiple',
            text: 'Какие цвета ассоциируются с вашим идеальным ароматом?',
            options: [
                {
                    text: 'Белый и светлые оттенки',
                    value: 'white_light',
                    keywords: ['чистый', 'невинный', 'clean', 'pure', 'innocent']
                },
                {
                    text: 'Розовый и персиковый',
                    value: 'pink_peach',
                    keywords: ['нежный', 'женственный', 'gentle', 'feminine', 'soft']
                },
                {
                    text: 'Золотой и янтарный',
                    value: 'gold_amber',
                    keywords: ['теплый', 'роскошный', 'warm', 'luxurious', 'rich']
                },
                {
                    text: 'Зеленый и природные тона',
                    value: 'green_natural',
                    keywords: ['природный', 'свежий', 'natural', 'green', 'herbal']
                },
                {
                    text: 'Синий и морские оттенки',
                    value: 'blue_marine',
                    keywords: ['прохладный', 'свежий', 'cool', 'aquatic', 'marine']
                },
                {
                    text: 'Темные и глубокие цвета',
                    value: 'dark_deep',
                    keywords: ['глубокий', 'таинственный', 'deep', 'mysterious', 'intense']
                }
            ]
        }
    ];

    // Метод для получения текущего вопроса
    getCurrentQuestion() {
        return this.questions[this.currentQuestion];
    }

    // Метод для ответа на вопрос
    answerQuestion(questionId, selectedValues) {
        this.answers[questionId] = selectedValues;
        
        // Сохраняем ответ в соответствующий блок профиля
        const question = this.questions.find(q => q.id === questionId);
        if (question) {
            this.profile[question.block][questionId] = selectedValues;
        }
    }

    // Переход к следующему вопросу
    nextQuestion() {
        if (this.currentQuestion < this.questions.length - 1) {
            this.currentQuestion++;
            return true;
        }
        return false;
    }

    // Переход к предыдущему вопросу
    previousQuestion() {
        if (this.currentQuestion > 0) {
            this.currentQuestion--;
            return true;
        }
        return false;
    }

    // Проверка завершения квиза
    isComplete() {
        return this.currentQuestion >= this.questions.length - 1;
    }

    // Получение всех ключевых слов из ответов
    getAllKeywords() {
        const keywords = [];
        
        for (const [questionId, answerValues] of Object.entries(this.answers)) {
            const question = this.questions.find(q => q.id === questionId);
            if (!question) continue;

            // Обрабатываем ответы (могут быть массивом или строкой)
            const values = Array.isArray(answerValues) ? answerValues : [answerValues];
            
            values.forEach(value => {
                const option = question.options.find(opt => opt.value === value);
                if (option && option.keywords) {
                    keywords.push(...option.keywords);
                }
            });
        }
        
        return keywords;
    }

    // Анализ профиля без весовых коэффициентов
    analyzeProfile() {
        const keywords = this.getAllKeywords();
        const keywordFrequency = {};
        
        // Подсчет частоты ключевых слов
        keywords.forEach(keyword => {
            keywordFrequency[keyword] = (keywordFrequency[keyword] || 0) + 1;
        });

        // Анализ по блокам Edwards Fragrance Wheel
        const edwardsAnalysis = {
            floral: 0,
            oriental: 0,
            woody: 0,
            fresh: 0
        };

        // Подсчет соответствий по семействам Edwards (улучшенная версия)
        const edwardsKeywords = {
            floral: ['floral', 'rose', 'jasmine', 'peony', 'lily', 'romantic', 'feminine', 'gentle', 'нежный', 'романтичный', 'чувственный', 'женственный'],
            oriental: ['oriental', 'amber', 'vanilla', 'musk', 'warm', 'spicy', 'exotic', 'intense', 'теплый', 'пряный', 'восточный', 'насыщенный', 'согревающий'],
            woody: ['woody', 'sandalwood', 'cedar', 'forest', 'pine', 'earthy', 'masculine', 'древесный', 'лесной', 'мужской', 'строгий'],
            fresh: ['fresh', 'citrus', 'green', 'aquatic', 'marine', 'clean', 'light', 'свежий', 'легкий', 'морской', 'чистый', 'прохладный', 'дневной', 'летний', 'весенний']
        };

        keywords.forEach(keyword => {
            const lowerKeyword = keyword.toLowerCase();
            
            // Проверяем принадлежность к каждому семейству
            Object.keys(edwardsKeywords).forEach(family => {
                if (edwardsKeywords[family].includes(lowerKeyword)) {
                    edwardsAnalysis[family]++;
                }
            });
        });

        // Определение доминирующих семейств с защитой от ошибок
        const totalScore = Object.values(edwardsAnalysis).reduce((sum, score) => sum + score, 0);
        const edwardsPercentages = {};
        
        for (const [family, score] of Object.entries(edwardsAnalysis)) {
            edwardsPercentages[family] = totalScore > 0 ? Math.round((score / totalScore) * 100) : 0;
        }

        // Находим доминирующее семейство с защитой от ошибок
        const dominantFamily = totalScore > 0 
            ? Object.keys(edwardsPercentages).reduce((a, b) => 
                edwardsPercentages[a] > edwardsPercentages[b] ? a : b
            )
            : 'fresh'; // По умолчанию, если нет данных

        return {
            profile: this.profile,
            keywords: keywords,
            keywordFrequency: keywordFrequency,
            edwardsAnalysis: edwardsPercentages,
            dominantFamily: dominantFamily,
            totalKeywords: keywords.length,
            uniqueKeywords: Object.keys(keywordFrequency).length,
            hasValidData: totalScore > 0
        };
    }

    // Получение рекомендаций на основе анализа
    getRecommendations() {
        const analysis = this.analyzeProfile();
        const recommendations = {
            fragranceTypes: [],
            brands: [],
            seasons: [],
            occasions: []
        };

        // Рекомендации на основе доминирующего семейства Edwards
        switch (analysis.dominantFamily) {
            case 'floral':
                recommendations.fragranceTypes = ['Цветочные', 'Цветочно-фруктовые', 'Цветочно-древесные'];
                recommendations.brands = ['Chanel', 'Dior', 'Guerlain', 'Marc Jacobs'];
                break;
            case 'oriental':
                recommendations.fragranceTypes = ['Восточные', 'Амбровые', 'Пряные'];
                recommendations.brands = ['Tom Ford', 'Yves Saint Laurent', 'Thierry Mugler'];
                break;
            case 'woody':
                recommendations.fragranceTypes = ['Древесные', 'Древесно-пряные', 'Древесно-цветочные'];
                recommendations.brands = ['Hermès', 'Creed', 'Maison Margiela'];
                break;
            case 'fresh':
                recommendations.fragranceTypes = ['Свежие', 'Цитрусовые', 'Водные'];
                recommendations.brands = ['Acqua di Parma', 'Dolce & Gabbana', 'Calvin Klein'];
                break;
        }

        return {
            analysis,
            recommendations
        };
    }

    // Сброс квиза
    reset() {
        this.currentQuestion = 0;
        this.answers = {};
        this.profile = {
            demographic: {},
            psychological: {},
            lifestyle: {},
            sensory: {},
            emotional: {}
        };
    }
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerfumeQuiz;
}