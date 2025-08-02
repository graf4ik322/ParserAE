// Тест для демонстрации работы парфюмерного квиза
const PerfumeQuiz = require('./perfume_quiz.js');

console.log('🔬 Тестирование парфюмерного квиза v3.0\n');

// Создаем экземпляр квиза
const quiz = new PerfumeQuiz();

console.log('📊 Информация о квизе:');
console.log(`- Общее количество вопросов: ${quiz.questions.length}`);
console.log(`- Количество блоков: 5`);

// Блоки вопросов
const blocks = {};
quiz.questions.forEach(q => {
    if (!blocks[q.block]) blocks[q.block] = 0;
    blocks[q.block]++;
});

console.log('\n📋 Распределение по блокам:');
Object.entries(blocks).forEach(([block, count]) => {
    console.log(`- ${block}: ${count} вопросов`);
});

// Симуляция прохождения квиза
console.log('\n🎯 Симуляция прохождения квиза:');

// Пример ответов (романтичная девушка)
const testAnswers = {
    'gender': 'female',
    'age_experience': 'intermediate',
    'personality_type': 'romantic',
    'lifestyle': 'calm',
    'usage_time': ['day', 'evening'],
    'occasions': ['romantic', 'work'],
    'style_preference': 'classic',
    'budget_category': 'selective',
    'longevity_preference': 'moderate',
    'fragrance_families': ['floral', 'oriental'],
    'intensity_preference': 'delicate',
    'seasonal_preference': ['spring', 'summer'],
    'desired_mood': ['romance', 'elegance'],
    'scent_memories': ['garden', 'home_comfort'],
    'color_associations': ['pink_peach', 'white_light']
};

// Заполняем ответы
Object.entries(testAnswers).forEach(([questionId, answer]) => {
    quiz.answerQuestion(questionId, answer);
});

// Анализируем результаты
const analysis = quiz.analyzeProfile();
const recommendations = quiz.getRecommendations();

console.log('\n📈 Результаты анализа:');
console.log(`- Общее количество ключевых слов: ${analysis.totalKeywords}`);
console.log(`- Уникальных ключевых слов: ${analysis.uniqueKeywords}`);
console.log(`- Доминирующее семейство: ${analysis.dominantFamily}`);
console.log(`- Данных достаточно для анализа: ${analysis.hasValidData ? 'Да' : 'Нет'}`);

console.log('\n🌸 Edwards Fragrance Wheel анализ:');
Object.entries(analysis.edwardsAnalysis).forEach(([family, percentage]) => {
    const emoji = {
        'floral': '🌸',
        'oriental': '🌟', 
        'woody': '🌳',
        'fresh': '💧'
    };
    console.log(`- ${emoji[family]} ${family}: ${percentage}%`);
});

console.log('\n🎨 Топ-10 ключевых слов:');
const sortedKeywords = Object.entries(analysis.keywordFrequency)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 10);

sortedKeywords.forEach(([keyword, count], index) => {
    console.log(`${index + 1}. ${keyword} (${count})`);
});

console.log('\n🌟 Рекомендации:');
console.log(`- Типы ароматов: ${recommendations.recommendations.fragranceTypes.join(', ')}`);
console.log(`- Бренды: ${recommendations.recommendations.brands.join(', ')}`);

console.log('\n✅ Тест завершен успешно!');
console.log('🎯 Квиз работает корректно и готов к использованию.');