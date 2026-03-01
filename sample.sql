/* =========================================================
   E-VOTING SYSTEM DATABASE
   Converted from ORACLE to MYSQL
   DO NOT CHANGE CONCEPT OR TABLE STRUCTURE
   ========================================================= */

-- =========================================================
-- 1️⃣ DATABASE CREATION (Oracle Tablespace + Schema → MySQL DB)
-- =========================================================
CREATE DATABASE secured_voting;
USE secured_voting;

-- =========================================================
-- 2️⃣ USER DETAILS TABLE
-- (Oracle SEQUENCE + DEFAULT → MySQL AUTO_INCREMENT)
-- =========================================================
CREATE TABLE v_user_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(50) NOT NULL,
    password VARCHAR(20) NOT NULL,
    last_login TIMESTAMP NULL
);

INSERT INTO v_user_detail (user_name, password)
VALUES ('user_1', 'user@123');

-- =========================================================
-- 3️⃣ VOTER ID DETAILS TABLE (AFTER SCAN)
-- =========================================================
CREATE TABLE v_voterid_details (
    voter_id VARCHAR(30),
    voter_name VARCHAR(256) NOT NULL,
    polling_status ENUM('NOT_POLLED', 'POLLED'),
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    polled_on TIMESTAMP NULL
);

CREATE INDEX v_voting_details_status_idx
ON v_voterid_details (polling_status);

INSERT INTO v_voterid_details (voter_id, voter_name, polling_status)
VALUES (101, 'A9F3XK29QZ...', 'NOT_POLLED');

-- =========================================================
-- 4️⃣ VOTER PRE-STORED DATA TABLE
-- (Oracle IDENTITY → MySQL AUTO_INCREMENT)
-- =========================================================
CREATE TABLE v_voterid_prestored_data (
    sno INT AUTO_INCREMENT PRIMARY KEY,
    voter_id VARCHAR(50) UNIQUE,
    voter_name VARCHAR(40),
    booth_name VARCHAR(20),
    pincode INT
);

INSERT INTO v_voterid_prestored_data
(voter_id, voter_name, booth_name, pincode)
VALUES ('voter001', 'votername01', 'kk nagar', 600078);
-- Single value update (same logic)
UPDATE v_voterid_prestored_data
SET voter_name = 'shamir'
WHERE voter_id = 'voter002';

-- =========================================================
-- 5️⃣ ADMIN DETAILS TABLE
-- =========================================================
CREATE TABLE v_admin_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(50) NOT NULL,
    password VARCHAR(20) NOT NULL,
    last_login TIMESTAMP NULL
);

INSERT INTO v_admin_detail (user_name, password, last_login)
VALUES ('admin_1', 'admin@123', CURRENT_TIMESTAMP);

CREATE TABLE vote_result (
    id INT AUTO_INCREMENT PRIMARY KEY,
    party_name VARCHAR(100) NOT NULL,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert some dummy data to verify the Admin Page works
INSERT INTO vote_result (party_name) VALUES ('Party 1'), ('Party 2'), ('Party 3');

-- =========================================================
-- 6️⃣ VERIFICATION QUERIES
-- =========================================================
SHOW TABLES;

SELECT * FROM v_user_detail;
SELECT * FROM v_voterid_details;
SELECT * FROM v_voterid_prestored_data;
SELECT * FROM v_admin_detail;
/* ================= END OF SCRIPT ================= */
