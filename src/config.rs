use strum::{Display, EnumIter};

fn get_env(key: &'static str) -> Option<String> {
  match std::env::var(key) {
    Ok(env) => Some(env),
    Err(err) => match err {
      std::env::VarError::NotPresent => None,
      std::env::VarError::NotUnicode(err) => {
        panic!("Os env `{key}`={err:?} is not a valid unicode")
      },
    },
  }
}

#[derive(PartialEq, Eq, PartialOrd, Ord, EnumIter, Display, Clone, Copy)]
pub enum ModelEndpoint {
  OpenAI,
  Cohere,
  Anyscale,
  HuggingFace,
  Vectara,
  Perplexity,
}

fn masked_string(input: &str) -> String {
  let len = input.chars().count();
  if len == 0 {
    return String::new();
  }
  if len <= 9 {
    let half = ((len as f64) / 2.0).ceil() as usize;
    format!(
      "{}{}",
      input.chars().take(half).collect::<String>(),
      "*".repeat(len - half)
    )
  } else {
    let start: String = input.chars().take(4).collect();
    let end: String = input.chars().skip(4).skip(len - 4 * 2).collect();
    format!("{start}*****{end}")
  }
}

impl ModelEndpoint {
  pub fn base_url(&self) -> &'static str {
    match self {
      Self::OpenAI => "https://api.openai.com/v1",
      Self::Cohere => "https://api.cohere.ai",
      Self::Anyscale => "https://api.endpoints.anyscale.com/v1",
      Self::HuggingFace => "https://api-inference.huggingface.co",
      Self::Vectara => "https://api.vectara.io",
      Self::Perplexity => "https://api.perplexity.ai",
    }
  }

  pub fn masked_credentials(&self, config: &Config) -> String {
    match self {
      Self::OpenAI => masked_string(&config.openai_api_key.clone().unwrap_or_default()),
      Self::Cohere => masked_string(&config.cohere_api_key.clone().unwrap_or_default()),
      Self::Anyscale => masked_string(&config.anyscale_api_key.clone().unwrap_or_default()),
      Self::HuggingFace => masked_string(&config.huggingface_api_key.clone().unwrap_or_default()),
      Self::Perplexity => masked_string(&config.perplexity_api_key.clone().unwrap_or_default()),
      Self::Vectara => {
        let Some(token) = &config.vectara_token else {
          return String::new();
        };
        format!(
          "customer_id={}, client_id={}, client_secret={}",
          masked_string(&token.client_id),
          masked_string(&token.customer_id),
          masked_string(&token.client_secret)
        )
      },
    }
  }
}

#[derive(Debug)]
pub struct Config {
  pub address: String,
  pub base_url: String,
  pub openai_api_key: Option<String>,
  pub cohere_api_key: Option<String>,
  pub anyscale_api_key: Option<String>,
  pub huggingface_api_key: Option<String>,
  pub perplexity_api_key: Option<String>,
  pub vectara_token: Option<VectaraToken>,
}

impl Config {
  pub fn from_env() -> Self {
    let address = get_env("LLAMA_PASS_ADDRESS").unwrap_or_else(|| "127.0.0.1:8000".to_string());
    Self {
      base_url: get_env("BASE_URL").unwrap_or_else(|| format!("http://{address}")),
      address,
      openai_api_key: get_env("OPENAI_API_KEY"),
      cohere_api_key: get_env("CO_API_KEY"),
      anyscale_api_key: get_env("ANYSCALE_API_KEY"),
      huggingface_api_key: get_env("HF_TOKEN"),
      perplexity_api_key: get_env("PERPLEXITY_API_KEY"),
      vectara_token: VectaraToken::from_env(),
    }
  }

  /// Returns currently available endpoints.
  pub fn available_endpoints(&self) -> Vec<ModelEndpoint> {
    use ModelEndpoint as E;
    let mut models = Vec::new();
    if self.openai_api_key.is_some() {
      models.push(E::OpenAI);
    }
    if self.cohere_api_key.is_some() {
      models.push(E::Cohere);
    }
    if self.anyscale_api_key.is_some() {
      models.push(E::Anyscale);
    }
    if self.huggingface_api_key.is_some() {
      models.push(E::HuggingFace);
    }
    if self.perplexity_api_key.is_some() {
      models.push(E::Perplexity);
    }
    if self.vectara_token.is_some() {
      models.push(E::Vectara);
    }
    models
  }

  /// Generate a bash compatible environment exports.
  pub fn user_env_file(&self) -> String {
    let mut str = String::new();
    for (key, value) in self.user_env() {
      str.push_str(&format!("export {key}=\"{value}\"\n"))
    }
    str
  }

  /// Get a list of env vars for user
  pub fn user_env(&self) -> Vec<(String, String)> {
    let mut user_env = Vec::new();
    let placeholder = String::from("LlaMaKey");
    if self.openai_api_key.is_some() {
      user_env.push((
        "OPENAI_BASE_URL".into(),
        format!("{}/openai", self.base_url),
      ));
      user_env.push(("OPENAI_API_KEY".into(), placeholder.clone()));
    }
    if self.cohere_api_key.is_some() {
      user_env.push(("CO_API_URL".into(), format!("{}/cohere", self.base_url)));
      user_env.push(("CO_API_KEY".into(), placeholder.clone()));
    }
    if self.anyscale_api_key.is_some() {
      user_env.push((
        "ANYSCALE_BASE_URL".into(),
        format!("{}/anyscale", self.base_url),
      ));
      user_env.push(("ANYSCALE_API_KEY".into(), placeholder.clone()));
    }
    if self.huggingface_api_key.is_some() {
      user_env.push((
        "HF_INFERENCE_ENDPOINT".into(),
        format!("{}/huggingface", self.base_url),
      ));
      user_env.push(("HF_TOKEN".into(), placeholder.clone()));
    }
    if self.perplexity_api_key.is_some() {
      user_env.push((
        "PERPLEXITY_BASE_URL".into(),
        format!("{}/perplexity", self.base_url),
      ));
      user_env.push(("PERPLEXITY_API_KEY".into(), placeholder.clone()));
    }
    if self.vectara_token.is_some() {
      user_env.push((
        "VECTARA_BASE_URL".into(),
        format!("{}/vectara", self.base_url),
      ));
      user_env.push(("VECTARA_CUSTOMER_ID".into(), placeholder.clone()));
      user_env.push(("VECTARA_CLIENT_ID".into(), placeholder.clone()));
      user_env.push(("VECTARA_CLIENT_SECRET".into(), placeholder.clone()));
    }

    user_env
  }
}

#[derive(Debug)]
pub struct VectaraToken {
  pub customer_id: String,
  pub client_id: String,
  pub client_secret: String,
}

impl VectaraToken {
  pub fn from_env() -> Option<Self> {
    Some(Self {
      customer_id: get_env("VECTARA_CUSTOMER_ID")?,
      client_id: get_env("VECTARA_CLIENT_ID")?,
      client_secret: get_env("VECTARA_CLIENT_SECRET")?,
    })
  }
}
