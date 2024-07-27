CREATE TABLE GunCrimes (
    DR_NO INT PRIMARY KEY,
    Gun_related BOOLEAN
);

DELIMITER $$

CREATE PROCEDURE IdentifyAndStoreGunCrimes()
BEGIN
    DECLARE v_DR_NO INT;
    DECLARE v_Crime_Description VARCHAR(255);
    DECLARE v_Weapon_Description VARCHAR(255);
    DECLARE v_Comment TEXT;
    DECLARE gunCount INT;
    DECLARE gunUsed BOOLEAN;
    DECLARE done INT DEFAULT 0;

    DECLARE gunCrimeCursor CURSOR FOR 
        SELECT CT.DR_NO, CT.Crime_Description, CD.Weapon_Description, CM.Comment
        FROM OutputTable CT
        LEFT OUTER JOIN CrimeDetail CD ON CT.DR_NO = CD.DR_NO
        LEFT OUTER JOIN Comment CM ON CT.DR_NO = CM.DR_NO;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    OPEN gunCrimeCursor;

    fetch_loop: LOOP
        FETCH gunCrimeCursor INTO v_DR_NO, v_Crime_Description, v_Weapon_Description, v_Comment;
        IF done THEN
            LEAVE fetch_loop;
        END IF;

        -- First advanced query
        SET gunCount = (
            SELECT COUNT(*) FROM (
                SELECT DR_NO
                FROM CrimeDetail
                WHERE v_Crime_Description LIKE '%GUN%' OR v_Crime_Description LIKE '%WEAPON%'
                
                UNION ALL

                SELECT DR_NO
                FROM Comment
                WHERE v_Comment LIKE '%GUN%' OR v_Comment LIKE '%gun%' OR v_Comment LIKE '%weapon%' OR v_Comment LIKE '%WEAPON%' OR v_Comment LIKE '%shot%' OR v_Comment LIKE '%fired%'

            ) AS CombinedCounts
        );

        -- Second advanced query
        SET gunUsed = (
            SELECT EXISTS (
                SELECT 1
                WHERE v_Weapon_Description LIKE '%GUN%' OR 
                      v_Weapon_Description LIKE '%WEAPON%'
            )
        );

        IF gunUsed THEN
            INSERT IGNORE INTO GunCrimes(DR_NO, Gun_related)
            VALUES (v_DR_NO, TRUE);
        ELSEIF gunCount > 1 THEN
            INSERT IGNORE INTO GunCrimes(DR_NO, Gun_related)
            VALUES (v_DR_NO, TRUE);
        ELSE 
            INSERT IGNORE INTO GunCrimes(DR_NO, Gun_related)
            VALUES (v_DR_NO, FALSE);
        END IF;
    END LOOP fetch_loop;

    CLOSE gunCrimeCursor;

END$$

DELIMITER ;
