CREATE DATABASE IF NOT EXISTS business;
USE business;

CREATE TABLE IF NOT EXISTS users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_name VARCHAR(50) NOT NULL,
  user_surname VARCHAR(50) NOT NULL,
  user_daddy VARCHAR(50),
  user_phone VARCHAR(20) NOT NULL UNIQUE,
  user_email VARCHAR(100) NOT NULL UNIQUE,
  user_passport VARCHAR(50) UNIQUE,
  user_password VARCHAR(255) NOT NULL,
  user_avatar LONGBLOB,
  account_status ENUM('verified', 'unverified') NOT NULL DEFAULT 'unverified',
  user_role ENUM('user', 'expert', 'admin') NOT NULL DEFAULT 'user',
  user_data JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS publics (
  id INT PRIMARY KEY AUTO_INCREMENT,
  public_creator INT NOT NULL,
  category ENUM('marketing', 'management', 'finance', 'hr', 'it', 'production', 'law', 'other') NOT NULL DEFAULT 'other',
  topic_name VARCHAR(255) NOT NULL,
  topic_name_en VARCHAR(255),
  topic_text TEXT NOT NULL,
  preview_image LONGBLOB,
  public_status ENUM('accept', 'reject', 'waiting') NOT NULL DEFAULT 'waiting',
  rejection_reason TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (public_creator) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS publication_stats (
  public_id INT PRIMARY KEY,
  likes INT NOT NULL DEFAULT 0,
  comments INT NOT NULL DEFAULT 0,
  views INT NOT NULL DEFAULT 0,
  FOREIGN KEY(public_id) REFERENCES publics(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  public_id INT NOT NULL,
  user_id INT NOT NULL,
  comment_text TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(public_id) REFERENCES publics(id) ON DELETE CASCADE,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);



CREATE TABLE IF NOT EXISTS likes (
  user_id INT NOT NULL,
  public_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, public_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (public_id) REFERENCES publics(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS views (
  id INT AUTO_INCREMENT PRIMARY KEY,
  public_id INT NOT NULL,
  user_id INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (public_id) REFERENCES publics(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS experts (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL UNIQUE,
  company VARCHAR(255) NOT NULL,
  position VARCHAR(100) NOT NULL,
  expertise VARCHAR(50) NOT NULL,
  other_expertise VARCHAR(100),
  experience TINYINT NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE if not exists business.expert_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    company VARCHAR(255) NOT NULL,
    position VARCHAR(100) NOT NULL,
    expertise VARCHAR(50) NOT NULL,
    other_expertise VARCHAR(100),
    experience TINYINT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);


CREATE TABLE IF NOT EXISTS quotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text TEXT NOT NULL,
    author VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS business.passport_requests (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  passport_issued_by VARCHAR(255) NOT NULL COMMENT 'Кем выдан паспорт',
  passport_issue_date DATE NOT NULL COMMENT 'Дата выдачи паспорта',
  passport_division_code VARCHAR(10) NOT NULL COMMENT 'Код подразделения',
  passport_series VARCHAR(4) NOT NULL COMMENT 'Серия паспорта',
  passport_number VARCHAR(6) NOT NULL COMMENT 'Номер паспорта',
  gender ENUM('male', 'female') NOT NULL COMMENT 'Пол',
  birth_date DATE NOT NULL COMMENT 'Дата рождения',
  birth_place VARCHAR(255) NOT NULL COMMENT 'Место рождения',
  passport_photo LONGBLOB COMMENT 'Фото разворота паспорта с основными данными',
  status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending' COMMENT 'Статус проверки',
  rejection_reason TEXT COMMENT 'Причина отказа',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  UNIQUE KEY unique_user_pending_request (user_id, status)  -- Простая уникальность (не идеально, но без ошибок)
);