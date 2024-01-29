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

#[derive(Debug)]
pub struct Config {
  pub address: String,
  pub base_url: String,
  pub openai_api_key: Option<String>,
  pub cohere_api_key: Option<String>,
  pub anyscale_api_key: Option<String>,
  pub huggingface_api_key: Option<String>,
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
      vectara_token: VectaraToken::from_env(),
    }
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
    if self.openai_api_key.is_some() {
      user_env.push(("OPENAI_BASE_URL".into(), self.base_url.clone()));
      user_env.push(("OPENAI_API_KEY".into(), "openai".into()));
    }
    if self.cohere_api_key.is_some() {
      user_env.push(("CO_API_URL".into(), self.base_url.clone()));
      user_env.push(("CO_API_KEY".into(), "cohere".into()));
    }
    if self.anyscale_api_key.is_some() {
      user_env.push(("ANYSCALE_BASE_URL".into(), self.base_url.clone()));
      user_env.push(("ANYSCALE_API_KEY".into(), "anyscale".into()));
    }
    if self.huggingface_api_key.is_some() {
      user_env.push(("HF_INFERENCE_ENDPOINT".into(), self.base_url.clone()));
      user_env.push(("HF_TOKEN".into(), "huggingface".into()));
    }
    if self.vectara_token.is_some() {
      user_env.push((
        "VECTARA_BASE_URL".into(),
        format!("{}/vectara", self.base_url),
      ));
      user_env.push(("VECTARA_CUSTOMER_ID".into(), "vectara-customer".into()));
      user_env.push(("VECTARA_CLIENT_ID".into(), "vectara-client".into()));
      user_env.push(("VECTARA_CLIENT_SECRET".into(), "vectara-secret".into()));
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
