USE business;

-- Функция для транслятора
DELIMITER //
CREATE FUNCTION transliterate_russian(input VARCHAR(255)) RETURNS VARCHAR(255)
DETERMINISTIC
BEGIN
    DECLARE output VARCHAR(255);
    
    SET output = LOWER(input);
    
    SET output = REPLACE(output, 'а', 'a');
    SET output = REPLACE(output, 'б', 'b');
    SET output = REPLACE(output, 'в', 'v');
    SET output = REPLACE(output, 'г', 'g');
    SET output = REPLACE(output, 'д', 'd');
    SET output = REPLACE(output, 'е', 'e');
    SET output = REPLACE(output, 'ё', 'yo');
    SET output = REPLACE(output, 'ж', 'zh');
    SET output = REPLACE(output, 'з', 'z');
    SET output = REPLACE(output, 'и', 'i');
    SET output = REPLACE(output, 'й', 'y');
    SET output = REPLACE(output, 'к', 'k');
    SET output = REPLACE(output, 'л', 'l');
    SET output = REPLACE(output, 'м', 'm');
    SET output = REPLACE(output, 'н', 'n');
    SET output = REPLACE(output, 'о', 'o');
    SET output = REPLACE(output, 'п', 'p');
    SET output = REPLACE(output, 'р', 'r');
    SET output = REPLACE(output, 'с', 's');
    SET output = REPLACE(output, 'т', 't');
    SET output = REPLACE(output, 'у', 'u');
    SET output = REPLACE(output, 'ф', 'f');
    SET output = REPLACE(output, 'х', 'h');
    SET output = REPLACE(output, 'ц', 'ts');
    SET output = REPLACE(output, 'ч', 'ch');
    SET output = REPLACE(output, 'ш', 'sh');
    SET output = REPLACE(output, 'щ', 'sch');
    SET output = REPLACE(output, 'ъ', '');
    SET output = REPLACE(output, 'ы', 'y');
    SET output = REPLACE(output, 'ь', '');
    SET output = REPLACE(output, 'э', 'e');
    SET output = REPLACE(output, 'ю', 'yu');
    SET output = REPLACE(output, 'я', 'ya');
    
    -- Замена пробелов и символов
    SET output = REPLACE(output, ' ', '-');
    SET output = REPLACE(output, '_', '-');
    SET output = REGEXP_REPLACE(output, '[^a-z0-9-]', '');
    
    -- Удаление повторяющихся дефисов
    WHILE (output LIKE '--%') DO
        SET output = REPLACE(output, '--', '-');
    END WHILE;
    
    -- Удаление дефисов в начале и конце
    IF (output LIKE '-%') THEN
        SET output = SUBSTRING(output, 2);
    END IF;
    
    IF (output LIKE '%-') THEN
        SET output = SUBSTRING(output, 1, CHAR_LENGTH(output)-1);
    END IF;
    
    RETURN output;
END //
DELIMITER ;

-- Триггеры 
DELIMITER //
CREATE TRIGGER fill_translit_on_insert
BEFORE INSERT ON publics
FOR EACH ROW
BEGIN
    SET NEW.topic_name_en = transliterate_russian(NEW.topic_name);
END //

CREATE TRIGGER update_translit_on_change
BEFORE UPDATE ON publics
FOR EACH ROW
BEGIN
    IF NEW.topic_name != OLD.topic_name THEN
        SET NEW.topic_name_en = transliterate_russian(NEW.topic_name);
    END IF;
END //

CREATE TRIGGER update_likes_count AFTER INSERT ON likes
FOR EACH ROW
BEGIN
  UPDATE publication_stats 
  SET likes = likes + 1 
  WHERE public_id = NEW.public_id;
END //

CREATE TRIGGER update_comments_count AFTER INSERT ON comments
FOR EACH ROW
BEGIN
  UPDATE publication_stats 
  SET comments = comments + 1 
  WHERE public_id = NEW.public_id;
END //

CREATE TRIGGER update_views_count AFTER INSERT ON views
FOR EACH ROW
BEGIN
  UPDATE publication_stats 
  SET views = views + 1 
  WHERE public_id = NEW.public_id;
END //

CREATE TRIGGER init_public_stats AFTER INSERT ON publics
FOR EACH ROW
BEGIN
  INSERT INTO publication_stats (public_id, likes, comments, views)
  VALUES (NEW.id, 0, 0, 0);
END //
DELIMITER ;

-- Триггер для добавления эксперта при изменении роли пользователя
DELIMITER //
CREATE TRIGGER after_user_role_update
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    IF NEW.user_role = 'expert' AND OLD.user_role != 'expert' THEN
        -- Проверяем, есть ли заявка у пользователя
        IF EXISTS (SELECT 1 FROM expert_requests WHERE user_id = NEW.id) THEN
            -- Копируем данные из заявки
            INSERT INTO experts (user_id, company, position, expertise, other_expertise, experience, description)
            SELECT 
                user_id, 
                company, 
                position, 
                expertise, 
                other_expertise, 
                experience, 
                description
            FROM expert_requests 
            WHERE user_id = NEW.id
            LIMIT 1;
        ELSE
            -- Создаем запись с минимальными данными
            INSERT INTO experts (user_id, company, position, expertise, experience)
            VALUES (NEW.id, 'Не указано', 'Не указано', 'other', 0);
        END IF;
    ELSEIF NEW.user_role != 'expert' AND OLD.user_role = 'expert' THEN
        DELETE FROM experts WHERE user_id = NEW.id;
    END IF;
END//
DELIMITER ;



-- Очищаем таблицу, если она уже существует
TRUNCATE TABLE quotes;

-- Добавляем 20 цитат с чистыми текстами
INSERT INTO quotes (text, author) VALUES
('Отличная платформа для профессионалов! Нашёл много полезной информации и новых партнёров.', 'Сергей Иванов'),
('Бизнес-Мост помог мне найти инвестора для стартапа. Очень благодарен сообществу!', 'Алексей Петров'),
('Здесь собраны действительно качественные материалы. Рекомендую всем предпринимателям!', 'Мария Сидорова'),
('Нашёл здесь решение проблемы, которая мучила нас месяцами. Спасибо экспертам!', 'Дмитрий Смирнов'),
('Лучшая бизнес-платформа в рунете. Регулярно нахожу здесь полезные контакты.', 'Анна Кузнецова'),
('Публикую статьи и получаю обратную связь от коллег. Отличный способ развиваться!', 'Иван Васильев'),
('Благодаря Бизнес-Мосту нашёл новых клиентов. Экономия на маркетинге значительная!', 'Елена Попова'),
('Здесь общаются настоящие профессионалы. Учиться есть у кого!', 'Андрей Соколов'),
('Мои статьи получают в 10 раз больше просмотров, чем в блоге. Отличная аудитория!', 'Ольга Михайлова'),
('Бизнес-Мост — это не просто соцсеть, а инструмент для роста. Используйте его!', 'Павел Фёдоров'),
('За месяц участия получил три деловых предложения. Результат превзошёл ожидания!', 'Наталья Николаева'),
('Теперь все мои сотрудники здесь. Так удобнее обмениваться опытом!', 'Артём Павлов'),
('Лучшее, что случилось с моим бизнесом в этом году. Спасибо команде!', 'Светлана Александрова'),
('Здесь нет фейков и пустых разговоров, только дело. Ценю это!', 'Михаил Дмитриев'),
('Мои вопросы получают ответы от практиков. Не приходится платить консультантам!', 'Татьяна Сергеева'),
('Платформа экономит мне время и деньги. Теперь все контакты в одном месте!', 'Виктор Иванов'),
('После публикации статьи ко мне обратились из крупной компании. Неожиданный бонус!', 'Екатерина Волкова'),
('Бизнес-Мост — это как деловой клуб, но онлайн. Удобно и эффективно!', 'Александр Белов'),
('Здесь я нашёл партнёра для нового проекта. Теперь работаем вместе!', 'Юлия Козлова'),
('Мой бизнес вырос на 30% благодаря контактам отсюда. Рекомендую всем!', 'Роман Лебедев');

DELIMITER //
CREATE TRIGGER prevent_duplicate_pending_requests
BEFORE INSERT ON passport_requests
FOR EACH ROW
BEGIN
    IF NEW.status = 'pending' THEN
        IF EXISTS (
            SELECT 1 
            FROM passport_requests 
            WHERE user_id = NEW.user_id AND status = 'pending'
        ) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'У пользователя уже есть заявка в статусе "pending"';
        END IF;
    END IF;
END //
DELIMITER ;
