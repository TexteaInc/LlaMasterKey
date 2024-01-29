use std::{fs::File, io::Write, sync::Arc};

use crate::Config;
use anyhow::{Context, Ok};
use axum::extract::State;
use hyper_rustls::HttpsConnector;
use hyper_util::{
  client::legacy::{connect::HttpConnector, Client},
  rt::TokioExecutor,
};
use indoc::formatdoc;

pub type HyperClient = Client<HttpsConnector<HttpConnector>, axum::body::Body>;

pub type ServerState = State<Arc<Server>>;

#[derive(Clone, Debug)]
pub struct Server {
  pub config: Arc<Config>,
  pub hyper_client: HyperClient,
}

impl Server {
  pub fn new() -> anyhow::Result<Self> {
    let config = Config::from_env();
    let user_env_file = config.user_env_file();
    let local_config_path = "./llamakey_local.env";
    File::create(local_config_path)
      .with_context(|| format!("Failed to create {local_config_path}"))?
      .write_all(user_env_file.as_bytes())
      .with_context(|| format!("Failed to write envs to {local_config_path}"))?;
    let message = formatdoc! { r#"
      Please tell your clients to set the following environment variables before
      running their code using the Python SDK of OpenAI/Cohere/etc.:
      {user_env_file}
      For convenience, the shell command to set such environment variables are
      written to `{local_config_path}`. Simply run `source {local_config_path}`
      to activate them.
      For example:
      source {local_config_path} && python3 -c "import openai; openai.Completion.create(...)"
      "#
    };
    log::warn!("{message}");

    let rustls_client = hyper_rustls::HttpsConnectorBuilder::new()
      .with_native_roots()
      .context("Failed to build HTTP client with native roots")?
      .https_or_http()
      .enable_http1()
      .build();

    let hyper_client: HyperClient = Client::builder(TokioExecutor::new()).build(rustls_client);

    Ok(Server {
      config: Arc::new(config),
      hyper_client,
    })
  }
}
