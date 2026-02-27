CREATE DATABASE IF NOT EXISTS secured_voting;
USE secured_voting;

CREATE TABLE v_user_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    last_login TIMESTAMP NULL DEFAULT NULL
);
INSERT INTO v_user_detail (user_name, password, last_login)
VALUES ('admin', 'admin@123', CURRENT_TIMESTAMP);

INSERT INTO v_user_detail (user_name, password)
VALUES ('user_1', 'user@123');

CREATE TABLE v_voterid_details (
    voter_id INT PRIMARY KEY,
    encryption_key VARCHAR(256) NOT NULL,
    polling_status ENUM('NOT_POLLED', 'POLLED') DEFAULT 'NOT_POLLED',
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    polled_on TIMESTAMP NULL
);

CREATE INDEX v_voter_status_idx
ON v_voterid_details (polling_status);

INSERT INTO v_voterid_details (voter_id, encryption_key)
VALUES (101, 'A9F3XK29QZ...');
CREATE TABLE v_voterid_prestored_data (
    sno INT AUTO_INCREMENT PRIMARY KEY,
    voter_id VARCHAR(50) UNIQUE NOT NULL,
    voter_name VARCHAR(40),
    booth_name VARCHAR(30),
    pincode INT
);
INSERT INTO v_voterid_prestored_data
(voter_id, voter_name, booth_name, pincode)
VALUES
('voter001', 'votername01', 'KK Nagar', 600078);

UPDATE v_voterid_prestored_data
SET voter_name = 'shamir'
WHERE voter_id = 'voter001';

CREATE TABLE v_admin_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    last_login TIMESTAMP NULL DEFAULT NULL
);
INSERT INTO v_admin_detail (user_name, password, last_login)
VALUES ('admin_1', 'admin@123', CURRENT_TIMESTAMP);

UPDATE v_voterid_details
SET polling_status = 'POLLED',
    polled_on = CURRENT_TIMESTAMP
WHERE voter_id = 101
AND polling_status = 'NOT_POLLED';

SHOW TABLES;

SELECT * FROM v_user_detail;
SELECT * FROM v_voterid_details;
SELECT * FROM v_voterid_prestored_data;
SELECT * FROM v_admin_detail;
