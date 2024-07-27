CREATE TABLE InvalidCrimeEntries (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    DR_NO INT,
    InvalidReason VARCHAR(255),
    Latitude DECIMAL(9,6),
    Longitude DECIMAL(9,6)
);


DELIMITER $$

CREATE TRIGGER CheckInsertionTrigger
BEFORE INSERT ON CrimeTable
FOR EACH ROW
BEGIN
    IF NOT (NEW.Latitude BETWEEN 33.70 AND 34.35 AND NEW.Longitude BETWEEN -118.67 AND -118.15) THEN
        INSERT INTO InvalidCrimeEntries (DR_NO, InvalidReason, Latitude, Longitude)
        VALUES (NEW.DR_NO, 'Location outside LA', NEW.Latitude, NEW.Longitude);
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid Input QAQ';
    END IF;
END$$

DELIMITER ;
