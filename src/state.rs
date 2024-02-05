use std::{fs::File, io::Write, process::exit, sync::Arc};

use crate::{Config, ModelEndpoint};
use anyhow::{Context, Ok};
use axum::extract::State;
use comfy_table::{presets::UTF8_NO_BORDERS, Cell, ContentArrangement, Row, Table};
use hyper_rustls::HttpsConnector;
use hyper_util::{
  client::legacy::{connect::HttpConnector, Client},
  rt::TokioExecutor,
};
use indoc::formatdoc;
use strum::IntoEnumIterator;

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

    let endpoints = config.available_endpoints();
    if endpoints.is_empty() {
      log::error!(
        "Based on your configuration, no endpoint is available. Please check your environment variables."
      );
      exit(1);
    } else {
      let mut available_msg = "API endpoints availability:\n".to_string();
      let mut table = Table::new();
      table
        .load_preset(UTF8_NO_BORDERS)
        .set_content_arrangement(ContentArrangement::Dynamic)
        .set_width(100)
        .set_header(vec![
          Cell::new("Name"),
          Cell::new("Base URL"),
          Cell::new("Credentials"),
        ]);

      for endpoint in ModelEndpoint::iter() {
        if endpoints.contains(&endpoint) {
          table.add_row(Row::from([
            format!("✓ {endpoint}"),
            endpoint.base_url().to_string(),
            endpoint.masked_credentials(&config),
          ]));
        } else {
          table.add_row(Row::from([
            format!("✗ {endpoint}"),
            "-".to_string(),
            "-".to_string(),
          ]));
        }
      }
      available_msg.push_str(&table.to_string());
      log::info!("{available_msg}");
    }

    let message = formatdoc! { r#"

      Please tell your clients to set the following environment variables before running their code using the Python SDK of OpenAI/Cohere/etc.:

      {user_env_file}

      For your convenience, the shell commands above are dumped to `{local_config_path}`. 
      Simply run `source {local_config_path}` on your client end to activate them. For example:
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
