

package mohit.org.main;


import mohit.org.test;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;




public class jenkins_tutorial {
    // Create a logger instance using Log4j
    private static final Logger logger = LogManager.getLogger(jenkins_tutorial.class);

    public jenkins_tutorial() {
        example(); // Call example method from constructor
    }

    public void example() {
        logger.info("Application started");
    }

    public static void main(String[] args){
        // Create an instance of the class to access the logger
        jenkins_tutorial tutorial = new jenkins_tutorial();
        tutorial.example();
        logger.info("Application executed");
    }
}
