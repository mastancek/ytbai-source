from typing import TypeVar, Callable, Optional, Type, Union, List
import time
from functools import wraps
import logging
from .exceptions import RetryError, NetworkError, APIError

T = TypeVar('T')

class RetryStrategy:
    """Strategie pro opakování pokusů"""
    def __init__(self, 
                 max_attempts: int = 3,
                 delay: float = 1.0,
                 backoff_factor: float = 2.0,
                 exceptions: Union[Type[Exception], List[Type[Exception]]] = (Exception,)):
        self.max_attempts = max_attempts
        self.delay = delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions if isinstance(exceptions, (list, tuple)) else [exceptions]

    def get_delay(self, attempt: int) -> float:
        """Vypočítá zpoždění pro další pokus"""
        return self.delay * (self.backoff_factor ** (attempt - 1))

def retry(strategy: Optional[RetryStrategy] = None):
    """Dekorátor pro opakování operací při selhání
    
    Args:
        strategy: Strategie pro opakování pokusů
    """
    if strategy is None:
        strategy = RetryStrategy()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(1, strategy.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(strategy.exceptions) as e:
                    last_exception = e
                    
                    # Logování pokusu
                    logging.warning(
                        f"Pokus {attempt}/{strategy.max_attempts} selhal pro {func.__name__}: {str(e)}"
                    )
                    
                    # Pokud není poslední pokus, čekáme
                    if attempt < strategy.max_attempts:
                        delay = strategy.get_delay(attempt)
                        logging.info(f"Čekám {delay:.1f}s před dalším pokusem...")
                        time.sleep(delay)
                    
            # Pokud všechny pokusy selhaly
            raise RetryError(
                f"Operace selhala po {strategy.max_attempts} pokusech",
                strategy.max_attempts,
                last_exception
            )
            
        return wrapper
    return decorator

# Předpřipravené strategie
DEFAULT_RETRY = RetryStrategy()

NETWORK_RETRY = RetryStrategy(
    max_attempts=5,
    delay=2.0,
    backoff_factor=2.0,
    exceptions=[NetworkError, ConnectionError, TimeoutError]
)

API_RETRY = RetryStrategy(
    max_attempts=3,
    delay=1.0,
    backoff_factor=2.0,
    exceptions=[APIError]
)

DOWNLOAD_RETRY = RetryStrategy(
    max_attempts=3,
    delay=5.0,
    backoff_factor=2.0,
    exceptions=[NetworkError, ConnectionError, TimeoutError]
) 