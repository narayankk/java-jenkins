package mohit.org.test;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

public class jenkins_tutorial {
    // Create a logger instance using Log4j
    private static final Logger logger = LogManager.getLogger(jenkins_tutorial.class);

    public jenkins_tutorial() {
        example(); // Call example method from constructor
    }

    public void example() {
        logger.info("Test Application started");
    }

    public void testExample() {
        logger.info("Test Example method executed");
    }
}


